from warning import getWarning, mkMap, mkImage
import sys
from os import remove
from os.path import dirname, abspath
from datetime import datetime, timezone, timedelta

sys.path.append(abspath("../"))
from pkg.twitter_python import tweet,uploadImage

args = sys.argv
print(args)

cityWarningData = getWarning()
"""
#デバッグ用でツイートしないよう注意
cityWarningData = [{
    '2520101': ['02','22','27','32','12','13','14','15'],
    '2520102': ['22'],
    '2520200': ['22'],
    '2520300': ['22'],
    '2520400': ['10'],
    '2520600': ['15'],
    '2520700': ['18'],
    '2520800': ['18'],
    '2520900': ['18'],
    '2521000': ['22'],
    '2521100': ['21'],
    '2521200': ['22'],
    '2521300': ['32'],
    '2521400': ['22'],
    '2538300': ['12'],
    '2538400': ['14'],
    '2542500': ['22'],
    '2544100': ['14'],
    '2544200': ['12'],
    '2544300': ['22']
},{'update': '2022-03-13T15:57:00+09:00', 'cityCount': 20, 'endWarning' : False}]
"""

dirName = dirname(abspath(__file__))
#時刻周りの生成
#now : 現在時刻
#jmaUpdate : 気象庁XMLアップデート
#jmaLastUpdate : 前回のアップデート
now = datetime.now(timezone(timedelta(hours=9)))
jmaUpdate = datetime.strptime(cityWarningData[1]['update'], '%Y-%m-%dT%H:%M:%S%z')
with open(f'{dirName}/tmp.txt') as f:
    jmaLastUpdate = f.read()
    jmaLastUpdate = datetime.strptime(jmaLastUpdate, '%Y-%m-%dT%H:%M:%S%z')

#警報等が一つ以上ある場合で前回より更新しているまたは、0分の場合
if cityWarningData[1]['cityCount'] > 0 and (jmaUpdate > jmaLastUpdate or now.minute == 0):
    wLevels = mkMap(cityWarningData[0])
    imageList = mkImage(cityWarningData[0])
    #画像リスト
    ids = []
    for path in imageList:
        id = uploadImage(path)
        ids.append(id)
    #以下ツイート文生成→ツイート
    tweetText = f'{now.day}日{now.hour}時{now.minute}分現在 #滋賀県 内'
    if cityWarningData[1]['cityCount'] == 20:
        tweetText += '全域に'
    else:
        tweetText += '一部地域に'
    alarts = []
    if wLevels[0]:
        alarts.append(' #特別警報 ')
    if wLevels[1]:
        alarts.append(' #警報 ')
    if wLevels[2]:
        alarts.append(' #注意報 ')
    tweetText += '、'.join(alarts) + 'が発令されています。\n'
    if wLevels[0]:
        tweetText += '大切な命を守るため、身の安全を確保してください。\n'
    tweetText += '#滋賀県気象情報\n'
    tweetText += f'(気象庁更新時刻 {jmaUpdate.day}日{jmaUpdate.hour}時{jmaUpdate.minute}分)'
    if args == ['main.py']:
        tweet(tweetText,mediaIDs=ids)
    elif args[1] == 'gitTest':
        print(tweetText)
    #画像の削除
    for path in imageList:
        remove(path)
    remove(f'{dirName}/warningMap.png')
#警報等がなくなった場合で前回のアップデート時間と違う場合
elif cityWarningData[1]["endWarning"] and  jmaUpdate > jmaLastUpdate:
    tweetText = f'{now.day}日{now.hour}時{now.minute}分現在 #滋賀県 内に発令されていた #注意報 #警報 は解除されました。 #滋賀県気象情報\n(気象庁更新時刻 {jmaUpdate.day}日{jmaUpdate.hour}時{jmaUpdate.minute}分)'
    if args == ['main.py']:
        tweet(tweetText)
    elif args[1] == 'gitTest':
        print(tweetText)
#気象庁のアップデート時間の更新(更新の有無に関わらず)
with open(f'{dirName}/tmp.txt', mode='w') as f:
    f.write(cityWarningData[1]['update'])