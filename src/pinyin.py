import numpy as np
import os, sys, fileinput, json


fir_p = {}  # 某字符出现在句首的概率对数 {str: float}
dou_count = {}  # 字符的二元出现次数 {str: {str: int}}
sin_count = {}  # 字符出现计数 {str: int}
pch = {}  # 拼音到字符的dict {pinyin: [chs]}
sin_total = 396468407


def load():
    global pch
    global fir_p
    global sin_count
    global dou_count
    with open('../data/pch.txt') as f:
        pch = eval(f.read())
    with open('../data/fir_p.txt') as f:
        fir_p = eval(f.read())
    with open('../data/sin_count.txt') as f:
        sin_count = eval(f.read())
    with open('../data/dou_count.json') as f:
        dou_count = json.load(fp=f)


def preload_sentences():
    path = '../作业资料/sina_news/'
    for file in os.listdir(path):
        if file[0] == '.': continue
        out = open('../data/sentences.txt', 'a')
        with open(path+file) as f:
            for line in f.readlines():
                str = eval(line)['html']
                pattern = r',|\.|/|;|\'|`|\[|\]|<|>|\?|:|"|\{|\}|\~|!|@|#|\$|%|\^|&|' \
                          r'\(|\)|-|=|\_|\+|，|。|、|；|‘|’|' \
                          r'【|】|·|！| |…|（|）|：|？|!|“|”|【|】|『|』|{|}|《|》'
                segs = [x for x in re.split(pattern, str) if len(x) > 1 and ord(x[0]) > 128]
                for s in segs:
                    out.write(s+'\n')


def preload():
    def addone(dict, key):
        if key in dict:
            dict[key] += 1
        else:
            dict[key] = 1

    def add2(dict, ch1, ch2):
        if ch1 in dict:
            d = dict[ch1]
            if ch2 in d:
                d[ch2] += 1
            else:
                d[ch2] = 1
        else:
            dict[ch1] = {ch2: 1}

    fir_count = {}
    fir_tot = 0
    for line in fileinput.input(['../data/sentences.txt']):
        addone(fir_count, line[0])
        fir_tot += 1
        if fir_tot % 100000 == 0:
            print(fir_tot)
        for ch in line:
            if ch != '\n':
                addone(sin_count, ch)
        for i in range(len(line) - 2):
            add2(dou_count, line[i], line[i+1])
    for ch in fir_count:
        fir_p[ch] = np.log(1.0 * fir_count[ch] / fir_tot)
    with open('../data/fir_p.txt', 'w') as f:
        f.write(str(fir_p))
    with open('../data/sin_count.txt', 'w') as f:
        f.write(str(sin_count))
    with open('../data/dou_count.json', 'w') as f:
        json.dump(dou_count, f)


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


def run(pylist, lam=0.99):
    for py in pylist:
        if py not in pch:
            return ['Wrong piyin']
    nodes = []

    # first layer
    nodes.append([node(x, fir_p.get(x, -25.0), None) for x in pch[pylist[0]]])

    # middle layers
    for i in range(len(pylist)):
        if i == 0:
            continue
        nodes.append([node(x, 0, None) for x in pch[pylist[i]]])
        for nd in nodes[i]:
            nd.pr = nodes[i - 1][0].pr + getpr(nodes[i - 1][0].ch, nd.ch, lam)
            nd.prev = nodes[i - 1][0]
            for prend in nodes[i - 1]:
                if prend.pr + getpr(prend.ch, nd.ch, lam) > nd.pr:
                    nd.pr = prend.pr + getpr(prend.ch, nd.ch, lam)
                    nd.prev = prend

    # back propagation
    nd = max(nodes[-1], key=lambda x: x.pr)
    chs = []
    while nd is not None:
        chs.append(nd.ch)
        nd = nd.prev
    return list(reversed(chs))


def pinyin2hanzi(str, lam):
    return ''.join(run(str.lower().split(), lam))


def test(input, output='../data/output.txt', lam = 0.9):
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
            mychs = pinyin2hanzi(pys, lam)
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
def test_class(input, output='../data/output.txt'):
    with open(input) as f:
        lines = [line for line in f]
    f = open(output, 'w')
    for i in range(len(lines)):
        pys = lines[i]
        mychs = pinyin2hanzi(pys)
        f.write(mychs+'\n')
    f.close()


if __name__ == '__main__':
    # preload()
    print('Pinyin(2-gram) is loading data...٩(๑>◡<๑)۶')
    load()
    print('Begin test...ヾ(=･ω･=)o')
    if len(sys.argv) == 3:
        test_class(sys.argv[1], sys.argv[2])
    else:
        print('Wrong form.')
