import json
import math
import time


###TODO コードを整形すること！！！！

# 元データに\がある場合は\\にしないとエラーになる
# py3.9以上が必須

def main():
    simaiList = []
    file = input("出力されたjsonのfile名を入力してください。:")
    time_sta = time.time()
    f = open(file, "r",encoding="utf-8")
    json_dict = json.load(f)
    f.close()

    laneList = []
    for data in (json_dict['timeline']['otherObjects']):
        if data['type'] == 3:
            left = int(data['value'][0])
            right = int(data['value'][2])
            tmp = left - right
            if tmp == -7 or tmp == 1:
                laneList.append(listAppend(left, data, True))
            elif tmp == 7 or tmp == -1:
                laneList.append(listAppend(left, data, False))
            else:
                print("lane init error")
    laneList.append([1, 9999, 1, 1, 9999, True])
    laneList = sorted(laneList, key=lambda x: x[4])
    print(laneList)

    # 1ノーツずつsimai形式にして格納
    # simai_list=((note_simaiedit,measureIndex,mposition.num,mposition.denom),)
    rotate = True  # True==1<8
    left = 0
    for note in (json_dict['timeline']['notes']):
        tmpdata = listAppend(note['horizontalPosition']['numerator'], note)
        if laneList[0][4] <= tmpdata[4]:
            print(laneList[0])
            rotate = laneList[0][5]
            left = laneList[0][0]
            laneList.pop(0)
        # ノーツが始点でなければスキップ
        if note['customProps']['type'] != 'start':
            continue

        # ノーツ種類毎に判定、リストに追加
        if note['type'] == 'TAP':
            noteSimai = str(notePosition(tmpdata[0], left, rotate))
            if exCheck(note):
                noteSimai = noteSimai + 'x'
            simaiList.append(listAppend(noteSimai, note))


        elif note['type'] == 'TOUCH':
            touchPointNum = note['horizontalPosition']['numerator']
            if touchPointNum % 2 == 0:
                noteSimai = 'B' + str(notePosition(int(touchPointNum / 2 + 1), left, rotate))
            else:
                noteSimai = 'E' + str(notePosition(int(touchPointNum / 2 + 1), left, rotate))
            simaiList.append(listAppend(noteSimai, note))


        elif note['type'] == 'TOUCH.C':
            if hnbCheck(note):
                noteSimai = 'Cf'
            else:
                noteSimai = 'C'
            simaiList.append(listAppend(noteSimai, note))


        elif note['type'] == 'TOUCHHOLD':
            endNote, tmp = endSearch(note['guid'], json_dict['timeline'])
            endNote = endNote[0]
            hnb = ''
            if hnbCheck(note):
                hnb = 'f'
            if not endNote:
                noteSimai = 'Ch' + hnb
            else:
                noteLen, denom = noteLength(note, endNote, True)
                noteSimai = 'Ch' + hnb + '[' + str(denom) + ':' + str(noteLen) + ']'
            holdErrorChech(note, endNote)
            simaiList.append(listAppend(noteSimai, note))


        elif note['type'] == 'HOLD':
            endNote, tmp = endSearch(note['guid'], json_dict['timeline'])
            endNote = endNote[0]
            ex = ''
            if exCheck(note):
                ex = 'x'
            if not endNote:
                noteSimai = str(notePosition(tmpdata[0], left, rotate)) + 'h' + ex
            else:
                noteLen, denom = noteLength(note, endNote, True)
                noteSimai = str(notePosition(tmpdata[0], left, rotate)) + 'h' + ex + '[' + str(
                    denom) + ':' + str(noteLen) + ']'
            holdErrorChech(note, endNote)
            simaiList.append(listAppend(noteSimai, note))


        else:  # Slideとくっつく可能性のあるもの
            noteSimai = str(notePosition(tmpdata[0], left, rotate))
            # BREAKの判定
            if note['type'] == 'BREAK':
                noteSimai = noteSimai + 'b'
            else:
                if exCheck(note):
                    noteSimai = noteSimai + 'x'
            # middleとendがあるか検証
            # 無ければbreak単体
            endNotes, mid = endSearch(note['guid'], json_dict['timeline'])
            if mid:
                midNotes = endNotes
                for midNote in midNotes:
                    endNote, tmp = endSearch(midNote[0], json_dict['timeline'])
                    endNote = endNote[0]
                    noteLen, denom = noteLength(note, endNote)
                    noteSimai = noteSimai + 'V' + str(notePosition(midNote[1], left, rotate)) + str(
                        notePosition(endNote[1], left, rotate)) + '[' + str(denom) + ':' + str(noteLen) + ']*'
            elif endNotes:
                for endNote in endNotes:
                    noteLen, denom = noteLength(note, endNote)
                    noteSimai = noteSimai + str(endNote[0]) + str(notePosition(endNote[1], left, rotate)) + '[' + str(
                        denom) + ':' + str(noteLen) + ']*'
            else:  # break
                noteSimai = noteSimai + 'x'  # x=dummy
            simaiList.append(listAppend(noteSimai[:-1], note))
    simaiList = sorted(simaiList, key=lambda x: x[4])

    # BPM情報を格納
    bpmList = []
    for data in (json_dict['timeline']['otherObjects']):
        if data['type'] == 0:
            if data['measurePosition']['numerator'] == 0:
                bpmSimai = '(' + str(data['value']) + ')'
                bpmList.append(listAppend(bpmSimai, data))
            else:
                bpmSimai = '(' + str(data['value']) + ')'
                data = listAppend(bpmSimai, data)
                i = 0
                for note in simaiList:
                    if note[4] >= data[4]:
                        simaiList.insert(i, data)
                        break
                    else:
                        i += 1
    bpmList.append(['', 9999, 0, 1, 9999])

    # EACH判定
    i = 0
    while 1:
        if i == len(simaiList) - 1:
            break
        while 1:
            if simaiList[i][4] == simaiList[i + 1][4]:
                if simaiList[i][0][-1] == ')':
                    simaiList[i][0] = simaiList[i][0] + simaiList[i + 1][0]
                else:
                    simaiList[i][0] = simaiList[i][0] + '/' + simaiList[i + 1][0]
                simaiList.pop(i + 1)
            else:
                break
        i += 1

    # 1小節毎に分母の公倍数を求める
    i = 0
    frame = 1
    denom = []
    denomList = []
    while 1:
        if i == len(simaiList):
            break
        if simaiList[i][4] >= frame:
            frame += 1
            denomList.append(math.lcm(*denom))
            denom = []
        else:
            denom.append(simaiList[i][3])
            i += 1
    denomList.append(math.lcm(*denom))
    print(denomList)
    print(simaiList)
    print(bpmList)

    # txtに出力
    txt = ('maidata.txt')
    f = open(txt, 'w')
    # メタデータ挿入
    if json_dict['difficulty'] == 0:
        lev = 1
    else:
        lev = json_dict['difficulty']
    f.write(
        f"&title={flashReplace(json_dict['name'])}\n&artist={flashReplace(json_dict['creator'])}\n&des=\n"
        f"&first={json_dict['startTime']}\n\n&lv_{lev}={json_dict['level']}\n&inote_{lev}=\n{bpmList[0][0]}")
    bpmList.pop(0)
    noteNum = 0
    simaiListLength = len(simaiList)
    print(denomList)
    for index in range(len(denomList)):
        if index == bpmList[0][1]:
            f.write(f"\n{bpmList[0][0]}")
            bpmList.pop(0)
        simaiDenom = '{' + str(denomList[index]) + '}'
        f.write(f'\n{simaiDenom}')
        for beat in range(denomList[index]):
            if index == simaiList[noteNum][1] and beat == simaiList[noteNum][2] * (
                    denomList[index] / simaiList[noteNum][3]):
                f.write(simaiList[noteNum][0] + ',')
                if noteNum < simaiListLength - 1:
                    noteNum += 1
            else:
                f.write(',')
    f.write('\n(1){1}\n,\nE')
    f.close()
    time_end = time.time()
    print((time_end - time_sta) * 1000, 'ms')


def exCheck(note):
    ex = note['customProps']['EX']
    if ex == "ex":
        return True
    else:
        return False


def hnbCheck(note):
    hanabi = note['customProps']['hanabi']
    if hanabi == "hanabi":
        return True
    else:
        return False


def endSearch(start_guid, dic):
    # dic==['timeline']
    # return (ノーツ種別,レーン番号,小節数,拍数（分子）,拍分母)
    noteList = []
    midList = []
    for noteline in dic['noteLines']:
        if noteline['head'] == start_guid:
            for note in (dic['notes']):
                if noteline['tail'] == note['guid']:
                    if note['customProps']['type'] == 'middle':  # V専用の分岐
                        midList.append([note['guid'], note['horizontalPosition']['numerator']])
                        continue
                    if note['type'] != 'SLIDE':
                        noteList.append([note['type'], note['horizontalPosition']['numerator'], note['measureIndex'],
                                         note['measurePosition']['numerator'],
                                         note['measurePosition']['denominator']])
                    else:
                        noteList.append([note['customProps']['name'], note['horizontalPosition']['numerator'],
                                         note['measureIndex'],
                                         note['measurePosition']['numerator'],
                                         note['measurePosition']['denominator']])
    if midList:
        return midList, True
    else:
        return noteList, False


def listAppend(noteSimai, note, *tf):
    if note['measurePosition']['numerator'] == 0:
        num = 0
        denom = 1
    else:
        gcd = math.gcd(note['measurePosition']['numerator'], note['measurePosition']['denominator'])
        num = int(note['measurePosition']['numerator'] / gcd)
        denom = int(note['measurePosition']['denominator'] / gcd)
    point = note['measureIndex'] + note['measurePosition']['numerator'] / note['measurePosition']['denominator']
    point = float('{:.4f}'.format(point))
    return [noteSimai, note['measureIndex'], num, denom, point, *tf]


def noteLength(note, endNote, *hold):
    rootDenom = math.lcm(note['measurePosition']['denominator'], endNote[4])
    noteLen = (endNote[2] - note['measureIndex']) * rootDenom + endNote[3] * (rootDenom / endNote[4]) - \
              note['measurePosition']['numerator'] * (
                      rootDenom / note['measurePosition']['denominator']) - rootDenom / 4
    if hold:
        noteLen += rootDenom / 4
    returnRootDenom = int(rootDenom / math.gcd(rootDenom, int(noteLen)))
    returnNoteLen = int(noteLen / math.gcd(rootDenom, int(noteLen)))

    return returnNoteLen, returnRootDenom


def flashReplace(str1):
    str1 = str1.replace(r'\\', '\￥').replace('&', '\＆').replace('+', '\＋').replace('%', '\％')
    return str1


def holdErrorChech(note, endNote):
    if endNote[1] != note['horizontalPosition']['numerator']:
        print("hold error:始点と終点の位置がズレています。\n", note['measureIndex'], note['measurePosition']['numerator'],
              note['measurePosition']['denominator'])


def notePosition(notePos, left=1, rotate=True):
    if rotate:
        notePos += left
        if notePos > 8:
            notePos -= 8
    else:
        notePos = left - notePos
        if notePos < 1:
            notePos += 8
    return notePos


main()
