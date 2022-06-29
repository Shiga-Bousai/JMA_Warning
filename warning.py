from datetime import datetime, timezone, timedelta

import requests
from sqlalchemy import null
import xmltodict
from PIL import Image, ImageDraw, ImageFont #pip install pillow-simd
import matplotlib.pyplot as plt
import geopandas as gpd

from os import remove
from os.path import dirname, abspath, join
import sys
sys.path.append(abspath("../"))
from pkg.twitter_python import tweet,uploadImage
dirName = dirname(abspath(__file__))

import mkTextAlert

imageBaseColor = "#313131"

fontpathGSG_B = join(dirName,abspath("../fonts/GenShinGothic-Bold.ttf"))
fontGSG_B35 = ImageFont.truetype(fontpathGSG_B, 35)
fontGSG_B40 = ImageFont.truetype(fontpathGSG_B, 40)
fontGSG_B50 = ImageFont.truetype(fontpathGSG_B, 50)

def jmaAPI(url):
    jmaReq = requests.get(url)
    jmaReq.encoding = 'utf-8'
    return xmltodict.parse(jmaReq.text)

"""
mkTextSettings = {
    'mainBaseColor' : '',
    'mainTextColor' : '',
    'headerBaseColor' : '',
    'headerTextColor' : ''
}
"""

def getWarning(lastUpdateTime, args):
    newestUpdateDatetime = None
    jmaListExtra = jmaAPI('https://www.data.jma.go.jp/developer/xml/feed/extra.xml')
    for listData in reversed(jmaListExtra["feed"]["entry"]):
        updateDatetime = datetime.strptime(listData["updated"], '%Y-%m-%dT%H:%M:%S%z')
        if listData["author"]["name"] == '彦根地方気象台' and updateDatetime >= lastUpdateTime:
            updateBool =  updateDatetime > lastUpdateTime
            if listData["title"] == '気象特別警報・警報・注意報':
                jmaDetail = jmaAPI(listData["id"])
                weatherWarningData(jmaDetail, updateBool, args)
            elif listData["title"] == '土砂災害警戒情報':
                jmaDetail = jmaAPI(listData["id"])
                landslideAlertInfo(jmaDetail, updateBool, args)
        elif listData["author"]["name"] == '環境省 気象庁'and listData["content"]["#text"] == '【滋賀県熱中症警戒アラート】' and updateDatetime > lastUpdateTime:
            jmaDetail = jmaAPI(listData["id"])
            mkTextSettings = {
                'mainBaseColor' : '#121212',
                'mainTextColor' : '#fcfefd',
                'headerBaseColor' : '#952091',
                'headerTextColor' : '#fcfefd',
            }
            onceAlert(jmaDetail, f'{dirName}/wTextImg/neccyuu.jpeg', mkTextSettings, args)
            newestUpdateDatetime = listData["updated"]
    return newestUpdateDatetime

def mkMap(cityCodeDict):
    shigaCity = gpd.read_file(f'{dirName}/mapData/N03-20210101_25_GML.geojson') #滋賀県内の市町データ取得
    ax = plt.subplots(1, 1, figsize=(8, 8))[1]
    wLevels = [False, False, False]
    def addCityMap(cityCodeDict, wCityCode):
        cNum = 0
        cityWarColor = imageBaseColor
        if cityCodeDict[wCityCode] != []:
            for wCode in cityCodeDict[wCityCode]:
                if int(wCode) >= 32:
                    cityCodeDict[wCityCode].pop(cNum)
                    cityCodeDict[wCityCode].insert(0, wCode)
                cNum+=1
            if int(cityCodeDict[wCityCode][0]) >= 32:
                cityWarColor = "#7030a0"
                wLevels[0] = True
            elif int(cityCodeDict[wCityCode][0]) <= 9:
                cityWarColor = "#fe0000"
                wLevels[1] = True
            else:
                cityWarColor = "#febe00"
                wLevels[2] = True
        if wCityCode == "2520102":
            #大津市北部用処理
            otsuCity = gpd.read_file(f'{dirName}/mapData/A32-16_25.geojson') #滋賀県内の学区分けのデータ
            otsuNoath = ["志賀中学校","葛川中学校","伊香立中学校"]
            filt = otsuCity[ otsuCity['A32_008'].isin(otsuNoath)]
            filt.plot(ax=ax, color='none', edgecolor='none', linestyle='--', linewidth=0.3)
            
            from shapely.ops import cascaded_union
            bound = gpd.GeoSeries(cascaded_union(filt.geometry))
            bound.plot(ax=ax, color='none', edgecolor='#010101', linewidth=1)
            otsuCity[otsuCity['A32_008'].isin(otsuNoath)].plot(ax=ax, color=cityWarColor, edgecolor='none', linestyle='--', linewidth=0.3)
        else:
            shigaCity[shigaCity['N03_007'].isin([wCityCode[:-2]])].plot(ax=ax, color=cityWarColor, edgecolor='#010101', linewidth=1)
    [addCityMap(cityCodeDict, wCityCode) for wCityCode in cityCodeDict]
    #琵琶湖描画処理
    rakeBiwa = gpd.read_file(f'{dirName}/mapData/W09-05-g_Lake.geojson') #全国の胡沼データ
    rakeBiwa = rakeBiwa[rakeBiwa['W09_001'].isin(['琵琶湖'])] #琵琶湖だけ抜き出す
    rakeBiwa.plot(ax=ax, color="#121212", edgecolor='#010101', linewidth=1)
    plt.axis('off')
    plt.savefig(f'{dirName}/warningMap.png', format="png", dpi=300, facecolor=imageBaseColor, edgecolor=imageBaseColor)

    return wLevels

def mkImage(cityWarningData):
    cityCode = {
        "2520101" : "大津市南部",
        "2520102" : "大津市北部",
        "2520200" : "彦根市",
        "2520300" : "長浜市",
        "2520400" : "近江八幡市",
        "2520600" : "草津市",
        "2520700" : "守山市",
        "2520800" : "栗東市",
        "2520900" : "甲賀市",
        "2521000" : "野洲市",
        "2521100" : "湖南市",
        "2521200" : "高島市",
        "2521300" : "東近江市",
        "2521400" : "米原市",
        "2538300" : "日野町",
        "2538400" : "竜王町",
        "2542500" : "愛荘町",
        "2544100" : "豊郷町",
        "2544200" : "甲良町",
        "2544300" : "多賀町"
    }
    weatherWarningDict = {
        "00" : "解除",
        "02" : "暴風雪",
        "03" : "大雨",
        "04" : "洪水",
        "05" : "暴風",
        "06" : "大雪",
        "07" : "波浪",
        "08" : "高潮",
        "10" : "大雨",
        "12" : "大雪",
        "13" : "風雪",
        "14" : "雷",
        "15" : "強風",
        "16" : "波浪",
        "17" : "融雪",
        "18" : "洪水",
        "19" : "高潮",
        "20" : "濃霧",
        "21" : "乾燥",
        "22" : "なだれ",
        "23" : "低温",
        "24" : "霜",
        "25" : "着氷",
        "26" : "着雪",
        "27" : "その他",
        "32" : "暴風雪",
        "33" : "大雨",
        "35" : "暴風",
        "36" : "大雪",
        "37" : "波浪",
        "38" : "高潮"
    }

    BaseBG = Image.new('RGBA', (1920, 1080), (49, 49, 49, 255))
    draw = ImageDraw.Draw(BaseBG)

    warningMap = Image.open(f'{dirName}/warningMap.png')
    warningMap = warningMap.crop((500, 0, 1900, 2400))
    warningMap = warningMap.resize((630, 1080))

    BaseBG.paste(warningMap)

    warnCityCount = 0
    textH = 100

    def addCityTxt(cityData, textH):
        textW = 720
        textBox = draw.multiline_textbbox((720,textH), cityData, font=fontGSG_B40,anchor='lm')
        textWidth = textBox[2] - textBox[0]
        draw.rectangle((textW - 10, textH - 23, textW + textWidth + 5, textH + 35), fill="#f1f1f1")
        draw.multiline_text((textW,textH + 5), cityData, font=fontGSG_B40,fill='#121212',anchor='lm')
        draw.rectangle(((textW - 5, textH + 33, textW + 1080, textH + 35)), fill="#f1f1f1") #下のバー描画
        textW = 720 + textWidth + 50
        print(cityWarningData[cWD])
        for wCode in cityWarningData[cWD]:
            if int(wCode) >= 32:
                boxFillColor = "#7030a0"
            elif int(wCode) <= 9:
                boxFillColor = "#fe0000"
            else:
                boxFillColor = "#febe00"
            text = weatherWarningDict[wCode]
            textBox = draw.multiline_textbbox((textW, textH-100), text, font=fontGSG_B50,anchor='lm')
            textWidth = textBox[2] - textBox[0]
            draw.rectangle((textW - 13, textH - 29, textW + textWidth + 13, textH + 31), fill=boxFillColor)
            draw.multiline_text((textW, textH + 1), text, font=fontGSG_B50,fill='#f1f1f1',anchor='lm', stroke_width=3, stroke_fill='#121212')
            textW = textBox[2] + 30

    for cWD in cityWarningData:
        if cityWarningData[cWD] != []:
            if warnCityCount == 10:
                BaseBG.save(f'{dirName}/WarningPost1.png')
                draw.rectangle(((630, 0, 1920, 1080)), fill="#313131") #すでに描画されてるものを隠す
                textH = 100
            addCityTxt(cityCode[cWD],textH)
            warnCityCount += 1
            textH += 95

    if warnCityCount <= 9:
        BaseBG.save(f'{dirName}/WarningPost1.png')
        return [f'{dirName}/WarningPost1.png']
    else:
        BaseBG.save(f'{dirName}/WarningPost2.png')
        return [f'{dirName}/WarningPost1.png',f'{dirName}/WarningPost2.png']

def weatherWarningData(jmaDetail, updateBool, args):
    now = datetime.now(timezone(timedelta(hours=9)))
    otherData = {}
    wCount = 0
    otherData["endWarning"] = True #解除 注意報なしチェック
    updatedDatetime = jmaDetail["Report"]["Control"]["DateTime"]
    otherData["update"] = updatedDatetime #アップロード時間追加
    cityWarningCode = {"2520101":[],"2520102":[],"2520200":[],"2520300":[],"2520400":[],"2520600":[],"2520700":[],"2520800":[],"2520900":[],"2521000":[],"2521100":[],"2521200":[],"2521300":[],"2521400":[],"2538300":[],"2538400":[],"2542500":[],"2544100":[],"2544200":[],"2544300":[]}
    for data in jmaDetail["Report"]["Body"]["Warning"][3]["Item"]:
        cityCode = data["Area"]["Code"] #市町識別コード
        if type(data["Kind"]) == list:
            for warning in data["Kind"]:
                if warning["Status"] not in ["解除", "発表警報・注意報はなし"]:
                    otherData["endWarning"] = False
                    wCount+=1
                    cityWarningCode[cityCode].append(warning["Code"])
        else:
            if data["Kind"]["Status"] not in ["解除", "発表警報・注意報はなし"]:
                otherData["endWarning"] = False
                wCount+=1
                cityWarningCode[cityCode].append(data["Kind"]["Code"])
    otherData['cityCount'] = wCount

    #jmaUpdate : 気象庁XMLアップデート時間
    jmaUpdate = datetime.strptime(otherData['update'], '%Y-%m-%dT%H:%M:%S%z')
    jmaUpdate = jmaUpdate + timedelta(hours=9)
    #警報等が一つ以上ある場合で前回より更新しているまたは、0分の場合
    if otherData['cityCount'] > 0 and (updateBool or now.minute == 0):
        wLevels = mkMap(cityWarningCode)
        imageList = mkImage(cityWarningCode)
        #画像リスト
        ids = []
        for path in imageList:
            id = uploadImage(path)
            ids.append(id)
        #以下ツイート文生成→ツイート
        tweetText = f'{now.day}日{now.hour}時{now.minute}分現在 #滋賀県 内'
        if otherData['cityCount'] == 20:
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
    elif updateBool and otherData["endWarning"]:
        tweetText = f'{now.day}日{now.hour}時{now.minute}分現在 #滋賀県 内に発令されていた #注意報 #警報 は解除されました。 #滋賀県気象情報\n(気象庁更新時刻 {jmaUpdate.day}日{jmaUpdate.hour}時{jmaUpdate.minute}分)'
        if args == ['main.py']:
            tweet(tweetText)
        elif args[1] == 'gitTest':
            print(tweetText)

def landslideAlertInfo(jmaLLADetail, updateBool, args):
    now = datetime.now(timezone(timedelta(hours=9)))
    endedBool = False
    cityCount = False
    #データのJSON化
    alertLv = {
        "発表" : [],
        "継続" : [],
        "解除" : []
    }
    for name in jmaLLADetail["Report"]["Body"]["Warning"]["Item"]:
        if name["Kind"]["Code"] in ['1','3']:
            if endedBool == False and name["Kind"]["Code"] == '3':
                endedBool = True
            cityCount = True
            alertLv[name["Kind"]["Status"]].append(name["Area"]["Name"])
    
    #一市町以上ある場合で、更新されたor0分の場合
    if cityCount and (updateBool or now.minute == 0):
        #気象庁電文描画
        headLineText = jmaLLADetail["Report"]["Head"]["Headline"]["Text"]
        warningTextImage = f'{dirName}/wTextImg/landslideAlertInfo.jpeg'

        mkTextAlert(
            outpputFile=warningTextImage,
            headerText='土砂災害警戒情報',
            mainText=headLineText,
            mainBaseColor='#121212',
            mainTextColor='#fcfefd',
            headerBaseColor='#952091',
            headerTextColor='#fcfefd',
            icon=None
        )

        if alertLv["発表"] != [] or alertLv["継続"] != []:
            tweetText = """#土砂災害警戒情報 発令中
土砂災害警戒区域等では土砂災害が発生しやすい状況になっています。
ハザードマップなどを確認し災害に備えてください。

滋賀県のハザードマップはこちら↓
https://shiga-bousai.jp/dmap/map/index?l=M_r_k_d_risk_map&f=0010011111101000000&b=google_base&z=10&x=15156480.5&y=4197618.7349338
"""     
        elif alertLv["発表"] == [] and alertLv["継続"] == [] and alertLv["解除"] != []:
            tweetText = "#土砂災害警戒情報 は解除されました。\n地盤が緩んでいるところもあります。引き続き警戒を。"

        id = uploadImage(warningTextImage)

        if args == ['main.py']:
            tweet(tweetText,mediaIDs=[id])
        elif args[1] == 'gitTest':
            print(tweetText)

        remove(warningTextImage)

def onceAlert(jmaDetail, outputDir, mkTextSettings, args):
    #更新さらた場合のみ
    infoType = jmaDetail['Report']['Head']['InfoType'] #情報提供タイプ
    headTitle = jmaDetail['Report']['Head']['Title'] #headerのタイトル
    headDatetime = jmaDetail['Report']['Head']['ReportDateTime'] #header datetime
    contentText = jmaDetail["Report"]["Body"]["Comment"]["Text"]['#text'] #気象庁電文描画

    print(
        infoType,
        headTitle,
        headDatetime,
        contentText,
        outputDir
    )

    mkTextAlert.main(
        outpputFile     = outputDir,
        headerText      = headTitle,
        mainText        = contentText,
        mainBaseColor   = mkTextSettings['mainBaseColor'],
        mainTextColor   = mkTextSettings['mainTextColor'],
        headerBaseColor = mkTextSettings['headerBaseColor'],
        headerTextColor = mkTextSettings['headerTextColor'],
        icon=None
    )

    if infoType in ['発表', '訂正', '遅延']:
        tweetText = f'[{infoType}]\n\n{headTitle}\n受信時刻 : {headDatetime}\n\n#滋賀県 #気象情報'
        print(tweetText)
    
    id = uploadImage(outputDir)
    
    if args == ['main.py']:
        tweet(tweetText,mediaIDs=[id])