from warning import getWarning, mkMap, mkImage

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
},{'update': '2022-03-13T15:57:00+09:00', 'cityCount': 20}]
"""

import sys
import os
sys.path.append(os.path.abspath("../"))
from pkg.twitter_python import tweet,uploadImage

from datetime import datetime, timezone, timedelta

now = datetime.now(timezone(timedelta(hours=9)))
jmalastUpdate = datetime.strptime(cityWarningData[1]['update'], '%Y-%m-%dT%H:%M:%S%z')

if cityWarningData[1]['cityCount'] > 0:
    wLevels = mkMap(cityWarningData[0])
    imageList = mkImage(cityWarningData[0])
    ids = []
    for path in imageList:
        id = uploadImage(path)
        ids.append(id)

    tweetText = f'{now.day}日{now.hour}時{now.minute}分現在 #滋賀県 内'
    if cityWarningData[1]['cityCount'] == 20:
        tweetText += '全域に'
    else:
        tweetText += '一部地域に'
    if wLevels[0]:
        tweetText += ' #特別警報 や'
    if wLevels[1]:
        tweetText += ' #警報 、'
    if wLevels[2]:
        tweetText += ' #注意報 '
    tweetText += 'が発令されています。\n'
    if wLevels[0]:
        tweetText += '大切な命を守るため、身の安全を確保してください。\n'
    tweetText += '#滋賀県気象情報\n'
    tweetText += f'(気象庁更新時刻 {jmalastUpdate.day}日{jmalastUpdate.hour}時{jmalastUpdate.minute}分)'
    #tweet(tweetText,mediaIDs=ids)
elif cityWarningData[1]["endWarning"] and  jmalastUpdate > now + timedelta(minutes=-1):
    tweetText = f'{now.day}日{now.hour}時{now.minute}分現在 #滋賀県 内に発令されていた #注意報 #警報 は解除されました。 #滋賀県気象情報\n(気象庁更新時刻 {jmalastUpdate.day}日{jmalastUpdate.hour}時{jmalastUpdate.minute}分)'
    #tweet(tweetText)

from os import remove
from os.path import dirname, abspath
dirName = dirname(abspath(__file__))

for path in imageList:
    remove(path)

remove(f'{dirName}/warningMap.png')