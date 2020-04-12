import sys, fileinput, json
import numpy as np


fir_p = {}  # 某字符出现在句首的概率对数 {str: float}
dou_count = {}  # 字符的二元出现次数 {(str, str): int}
tri_count = {}  # 字符的三元出现次数 {str: {str: {str: int}}}
sin_count = {}  # 字符出现计数 {str: int}
pch = {}  # 拼音到字符的dict {pinyin: [chs]}
sin_total = 396468407


def preload3():
    def add3(dict, ch1, ch2, ch3):
        if ch1 in dict:
            d2 = dict[ch1]
            if ch2 in d2:
                d3 = d2[ch2]
                if ch3 in d3:
                    d3[ch3] += 1
                else:
                    d3[ch3] = 1
            else:
                d2[ch2] = {ch3: 1}
        else:
            dict[ch1] = {ch2: {ch3: 1}}

    count = 0
    for line in fileinput.input(['../data/sentences.txt']):
        if count % 100000 == 0:
            print('line:', count)
        if count > 31000000: break
        count += 1
        for i in range(len(line) - 3):
            add3(tri_count, line[i], line[i+1], line[i+2])
    with open('../data/tri_count.json', 'w') as f:
        json.dump(tri_count, f)


def load3():
    global pch
    global fir_p
    global sin_count
    global dou_count
    global tri_count
    with open('../data/pch.txt') as f:
        pch = eval(f.read())
    with open('../data/fir_p.txt') as f:
        fir_p = eval(f.read())
    with open('../data/sin_count.txt') as f:
        sin_count = eval(f.read())
    with open('../data/dou_count.json') as f:
        dou_count = json.load(fp=f)
    with open('../data/tri_count.json') as f:
        tri_count = json.load(fp=f)


class node():
    def __init__(self, ch, pr, prev):
        self.ch = ch
        self.pr = pr
        self.prev = prev


def getpr(ch1, ch2, lam):
    dd = {}
    douc = dou_count.get(ch1, dd).get(ch2, 0)
    sinc1 = sin_count.get(ch1, 0)
    if sinc1 > 0:
        sinc2 = sin_count.get(ch2, 0)
        res = np.log(lam * douc / sinc1 + (1 - lam) * sinc2 / sin_total)
    else:
        res = -50
    return res


def getpr3(ch1, ch2, ch3, lam):
    lam2 = 0.99
    dd = {}
    tric = tri_count.get(ch1, dd).get(ch2, dd).get(ch3, 0)
    douc = dou_count.get(ch1, dd).get(ch2, 0)
    if douc > 0:
        sinc3 = sin_count.get(ch3, 0)
        res = np.log(lam2 * tric / douc + (1 - lam2) * sinc3 / sin_total)
    else:
        res = -20
    res += getpr(ch2, ch3, lam)
    return res


def run3(pylist, lam=0.99):
    for py in pylist:
        if py not in pch:
            return ['Wrong pinyin format.']
    nodes = []

    # first layer
    nodes.append([node(x, fir_p.get(x, -20.0), None) for x in pch[pylist[0]]])

    # second layer
    if len(pylist) > 1:
        nodes.append([node(x, 0, None) for x in pch[pylist[1]]])
        for nd in nodes[1]:
            nd.pr = nodes[0][0].pr + getpr(nodes[1][0].ch, nd.ch, lam)
            nd.prev = nodes[0][0]
            for prend in nodes[0]:
                pr = getpr(prend.ch, nd.ch, lam)
                if prend.pr + pr > nd.pr:
                    nd.pr = prend.pr + pr
                    nd.prev = prend

    # middle layers
    for i in range(len(pylist)):
        if i < 2:
            continue
        nodes.append([node(x, 0, None) for x in pch[pylist[i]]])
        for nd in nodes[i]:
            nd.pr = nodes[i - 1][0].pr + getpr3(nodes[i - 1][0].prev.ch, nodes[i - 1][0].ch, nd.ch, lam)
            nd.prev = nodes[i - 1][0]
            for prend in nodes[i - 1]:
                pr3 = getpr3(prend.prev.ch, prend.ch, nd.ch, lam)
                if prend.pr + pr3 > nd.pr:
                    nd.pr = prend.pr + pr3
                    nd.prev = prend

    # back propagation
    nd = max(nodes[-1], key=lambda x: x.pr)
    chs = []
    while nd is not None:
        chs.append(nd.ch)
        nd = nd.prev
    return list(reversed(chs))


def pinyin2hanzi3(str):
    return ''.join(run3(str.lower().split()))


#自己测试用
def test3(input, output='../data/output.txt'):
    chcount = 0
    chcorrect = 0
    sencount = 0
    sencorrect = 0
    with open(input) as f:
        lines = [line for line in f]
    pys = ''
    chs = ''
    mychs = ''
    f = open(output, 'w')
    for i in range(len(lines)):
        if i % 2 == 0:
            pys = lines[i]
        else:
            chs = lines[i]
            mychs = pinyin2hanzi3(pys)
            f.write(pys+mychs+'\n')
            if chs[: len(mychs)] == mychs:
                sencorrect += 1
            sencount += 1
            for j in range(len(mychs)):
                if chs[j] == mychs[j]:
                    chcorrect += 1
                chcount += 1
    print('Sentences:{}, Correct sentences:{}, Correct rate:{}%'
          .format(sencount, sencorrect, round(100.0 * sencorrect / sencount, 2)))
    print('Characters:{},Correct characters:{}, Correct rate:{}%'
          .format(chcount, chcorrect, round(100.0 * chcorrect / chcount, 2)))
    f.close()


# 课程测试用
def test3_class(input, output='../data/output.txt'):
    with open(input) as f:
        lines = [line for line in f]
    f = open(output, 'w')
    for i in range(len(lines)):
        pys = lines[i]
        mychs = pinyin2hanzi3(pys)
        f.write(mychs+'\n')
    f.close()


if __name__ == '__main__':
    # preload3()
    print('Pinyin(3-gram) is loading data...٩(๑>◡<๑)۶')
    load3()
    print('Begin testヾ(=･ω･=)o')
    if len(sys.argv) == 3:
        test3_class(sys.argv[1], sys.argv[2])
    else:
        print('Wrong form.')
