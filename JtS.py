import json
import math
import time


###TODO コードを整形すること！！！！

# 元データに\がある場合は\\にしないとエラーになる
# py3.9以上が必須

def main():
    simai_list = []
    file = input("出力されたjsonのfile名を入力してください。:")
    time_sta = time.time()
    f = open(file, "r")
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
    rotate = False
    for note in (json_dict['timeline']['notes']):
        tmpdata = listAppend(note['horizontalPosition']['numerator'], note)
        if laneList[0][4] <= tmpdata[4]:
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
            simai_list.append(listAppend(noteSimai, note))


        elif note['type'] == 'TOUCH':
            touchPointNum = note['horizontalPosition']['numerator']
            if touchPointNum % 2 == 0:
                noteSimai = 'B' + str(int(touchPointNum / 2 + 1))
            else:
                noteSimai = 'E' + str(int(touchPointNum / 2 + 1))
            simai_list.append(listAppend(noteSimai, note))


        elif note['type'] == 'TOUCH.C':
            if hnbCheck(note):
                noteSimai = 'Cf'
            else:
                noteSimai = 'C'
            simai_list.append(listAppend(noteSimai, note))


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
            simai_list.append(listAppend(noteSimai, note))


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
            simai_list.append(listAppend(noteSimai, note))


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
            simai_list.append(listAppend(noteSimai[:-1], note))
    simai_list = sorted(simai_list, key=lambda x: x[4])

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
                for note in simai_list:
                    if note[4] >= data[4]:
                        simai_list.insert(i, data)
                        break
                    else:
                        i += 1
    bpmList.append(['', 9999, 0, 1, 9999])

    # EACH判定
    i = 0
    while 1:
        if i == len(simai_list) - 1:
            break
        while 1:
            if simai_list[i][4] == simai_list[i + 1][4]:
                if simai_list[i][0][-1] == ')':
                    simai_list[i][0] = simai_list[i][0] + simai_list[i + 1][0]
                else:
                    simai_list[i][0] = simai_list[i][0] + '/' + simai_list[i + 1][0]
                simai_list.pop(i + 1)
            else:
                break
        i += 1

    # 1小節毎に分母の公倍数を求める
    i = 1
    denom = []
    denomList = []
    for note in simai_list:
        if note[4] >= i:
            i += 1
            denomList.append(math.lcm(*denom))
            denom = []
        denom.append(note[3])
    denomList.append(math.lcm(*denom))

    print(simai_list)
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
    print(denomList)
    for index in range(len(denomList)):
        if index == bpmList[0][1]:
            f.write(f"\n{bpmList[0][0]}")
            bpmList.pop(0)
        simaiDenom = '{' + str(denomList[index]) + '}'
        f.write(f'\n{simaiDenom}')
        for beat in range(denomList[index]):
            if index == simai_list[noteNum][1] and beat == simai_list[noteNum][2] * (
                    denomList[index] / simai_list[noteNum][3]):
                f.write(simai_list[noteNum][0] + ',')
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
