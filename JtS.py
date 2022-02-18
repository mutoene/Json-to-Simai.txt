import json
import math
import time


# 元データに\がある場合は\\にしないとエラーになる

def main():
    time_sta = time.time()
    simai_list = []
    file = "test_tf.json"
    f = open(file, "r")
    json_dict = json.load(f)
    f.close()

    # 1ノーツずつ検証して二次元リストに格納
    # simai_list=((note_simaiedit,measureIndex,mposition.num,mposition.denom),)
    for note in (json_dict['timeline']['notes']):
        # ノーツが始点でなければスキップ
        if note['customProps']['type'] != 'start':
            continue

        # ノーツ種類毎に判定、リストに追加
        if note['type'] == 'TAP':
            noteSimai = str(note['horizontalPosition']['numerator'] + 1) + 'x'
            if not exCheck(note):
                noteSimai = noteSimai[:-1]
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
                # holdが同じレーンに設置されているかチェック
                if endNote[1] != note['horizontalPosition']['numerator']:
                    print("hold error", note['measureIndex'], note['measurePosition']['numerator'],
                          note['measurePosition']['denominator'])

                noteLen, denom = noteLength(note['measureIndex'], note['measurePosition']['numerator'],
                                            note['measurePosition']['denominator'], endNote[2], endNote[3],
                                            endNote[4])
                noteSimai = 'Ch' + hnb + '[' + str(denom) + ':' + str(noteLen) + ']'
            simai_list.append(listAppend(noteSimai, note))


        elif note['type'] == 'HOLD':
            endNote, tmp = endSearch(note['guid'], json_dict['timeline'])
            endNote = endNote[0]
            if not endNote:
                noteSimai = str(note['horizontalPosition']['numerator'] + 1) + 'h'
            else:
                if endNote[1] != note['horizontalPosition']['numerator']:
                    print("hold error", note['measureIndex'], note['measurePosition']['numerator'],
                          note['measurePosition']['denominator'])
                noteLen, denom = noteLength(note['measureIndex'], note['measurePosition']['numerator'],
                                            note['measurePosition']['denominator'], endNote[2], endNote[3],
                                            endNote[4])
                noteSimai = str(note['horizontalPosition']['numerator'] + 1) + 'h[' + str(denom) + ':' + str(
                    noteLen) + ']'
            simai_list.append(listAppend(noteSimai, note))


        elif note['type'] == 'BREAK':
            endNotes, tmp = endSearch(note['guid'], json_dict['timeline'])
            if not endNotes:
                simai_list.append(listAppend(str(note['horizontalPosition']['numerator'] + 1) + 'b', note))
            elif mid:
                midNotes = endNotes
                noteSimai = str(note['horizontalPosition']['numerator'] + 1)
                for midNote in midNotes:
                    endNote, tmp = endSearch(midNote[0], json_dict['timeline'])
                    endNote = endNote[0]
                    noteLen, denom = noteLength(note['measureIndex'], note['measurePosition']['numerator'],
                                                note['measurePosition']['denominator'], endNote[2], endNote[3],
                                                endNote[4])
                    noteSimai = noteSimai + 'V' + str(midNote[1] + 1) + str(
                        endNote[1] + 1) + '[' + str(denom) + ':' + str(noteLen) + ']*'
                    simai_list.append([noteSimai, note['measureIndex'],
                                       note['measurePosition']['numerator'], note['measurePosition']['denominator'],
                                       note['measureIndex'] +
                                       note['measurePosition']['numerator'] / note['measurePosition']['denominator']])
            else:
                noteSimai = str(note['horizontalPosition']['numerator'] + 1) + 'b'
                for endNote in endNotes:
                    noteLen, denom = noteLength(note['measureIndex'], note['measurePosition']['numerator'],
                                                note['measurePosition']['denominator'], endNote[2], endNote[3],
                                                endNote[4])
                    noteSimai = noteSimai + str(endNote[0]) + str(endNote[1] + 1) + '[' + str(denom) + ':' + str(
                        noteLen) + ']*'
                simai_list.append(listAppend(noteSimai[:-1], note))


        else:
            endNotes, mid = endSearch(note['guid'], json_dict['timeline'])
            if mid:
                midNotes = endNotes
                noteSimai = str(note['horizontalPosition']['numerator'] + 1)
                for midNote in midNotes:
                    endNote, tmp = endSearch(midNote[0], json_dict['timeline'])
                    endNote = endNote[0]
                    noteLen, denom = noteLength(note['measureIndex'], note['measurePosition']['numerator'],
                                                note['measurePosition']['denominator'], endNote[2], endNote[3],
                                                endNote[4])
                    noteSimai = noteSimai + 'V' + str(midNote[1] + 1) + str(
                        endNote[1] + 1) + '[' + str(denom) + ':' + str(noteLen) + ']*'
                    simai_list.append([noteSimai, note['measureIndex'],
                                       note['measurePosition']['numerator'], note['measurePosition']['denominator'],
                                       note['measureIndex'] +
                                       note['measurePosition']['numerator'] / note['measurePosition']['denominator']])
            else:
                noteSimai = str(note['horizontalPosition']['numerator'] + 1)
                for endNote in endNotes:
                    noteLen, denom = noteLength(note['measureIndex'], note['measurePosition']['numerator'],
                                                note['measurePosition']['denominator'], endNote[2], endNote[3],
                                                endNote[4])
                    noteSimai = noteSimai + str(endNote[0]) + str(endNote[1] + 1) + '[' + str(denom) + ':' + str(
                        noteLen) + ']*'
                    simai_list.append([noteSimai[:-1], note['measureIndex'],
                                       note['measurePosition']['numerator'], note['measurePosition']['denominator'],
                                       note['measureIndex'] + note['measurePosition']['numerator'] /
                                       note['measurePosition']['denominator']])

    for note in simai_list:
        note[4] = float('{:.4f}'.format(note[4]))

    # BPM情報を格納
    bpmList = []
    for note in (json_dict['timeline']['otherObjects']):
        bpmList.append([note['value'], note['measureIndex'],
                        note['measurePosition']['numerator'], note['measurePosition']['denominator'],
                        note['measureIndex'] + note['measurePosition']['numerator'] / note['measurePosition'][
                            'denominator']])
    simai_list = sorted(simai_list, key=lambda x: x[4])
    print(simai_list)

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

    for note in simai_list:
        pass

    txt = ('test.txt')
    f = open(txt, 'w')
    # メタデータ挿入
    if json_dict['difficulty'] == 0:
        lev = 1
    else:
        lev = json_dict['difficulty']
    f.write(
        f"&title={flashReplace(json_dict['name'])}\n&artist={flashReplace(json_dict['creator'])}\n&des=\n"
        f"&first={json_dict['startTime']}\n\n&lv_{lev}={json_dict['level']}\n&inote_{lev}=\n")
    f.close()
    time_end = time.time()
    print((time_end - time_sta) * 1000, 'ms')


def exCheck(note):
    ex = note['customProps']['EX?']
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
    elif noteList:
        return noteList, False
    else:
        return False, False


def listAppend(noteSimai, note):
    return [noteSimai, note['measureIndex'],
            note['measurePosition']['numerator'], note['measurePosition']['denominator'],
            note['measureIndex'] + note['measurePosition']['numerator'] / note['measurePosition'][
                'denominator']]


def noteLength(startIndex, startNum, startDenom, endIndex, endNum, endDenom):
    rootDenom = math.lcm(startDenom, endDenom)
    noteLen = (endIndex - startIndex) * rootDenom + endNum * (rootDenom / endDenom) - startNum * (
            rootDenom / startDenom)
    return int(noteLen), rootDenom


def flashReplace(str1):
    str1 = str1.replace(r'\\', '\￥').replace('&', '\＆').replace('+', '\＋').replace('%', '\％')
    return str1


main()
