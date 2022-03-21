import requests
from os.path import dirname, abspath, join
dirName = dirname(abspath(__file__))

imageBaseColor = "#313131"

import xmltodict
def jmaAPI(url):
    jmaReq = requests.get(url)
    jmaReq.encoding = 'utf-8'
    return xmltodict.parse(jmaReq.text)

def getWarning():
    cityWarningCode = {"2520101":[],"2520102":[],"2520200":[],"2520300":[],"2520400":[],"2520600":[],"2520700":[],"2520800":[],"2520900":[],"2521000":[],"2521100":[],"2521200":[],"2521300":[],"2521400":[],"2538300":[],"2538400":[],"2542500":[],"2544100":[],"2544200":[],"2544300":[]}
    otherData = {}
    wCount = 0
    jmaList = jmaAPI('https://www.data.jma.go.jp/developer/xml/https_feed/extra.xml')
    for listData in jmaList["feed"]["entry"]:
        if listData["author"]["name"] == '彦根地方気象台' and listData["title"] == '気象特別警報・警報・注意報':
            otherData["update"] = listData["updated"] #アップロード時間追加
            otherData["endWarning"] = True #解除 注意報なしチェック
            jmaDetail = jmaAPI(listData["id"])
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
            break
    otherData['cityCount'] = wCount
    return [cityWarningCode, otherData]

import matplotlib.pyplot as plt
import geopandas as gpd
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
            elif int(cityCodeDict[wCityCode][0]) <= 10:
                cityWarColor = "#fe0000"
                wLevels[1] = True
            else:
                cityWarColor = "#febe00"
                wLevels[2] = True
        if wCityCode == "2520102":
            #大津市北部用処理
            otsuCity = gpd.read_file(f'{dirName}/mapData/shape/A32-16_25.shp',encoding='SHIFT-JIS') #滋賀県内の学区分けのデータ
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
    rakeBiwa = gpd.read_file(f'{dirName}/mapData/W09-05_GML/W09-05-g_Lake.shp',encoding='SHIFT-JIS') #全国の胡沼データ
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

    from PIL import Image, ImageDraw, ImageFont #pip install pillow-simd

    BaseBG = Image.new('RGBA', (1920, 1080), (49, 49, 49, 255))
    draw = ImageDraw.Draw(BaseBG)
    fontpathGSG_B = join(dirName,abspath("../fonts/GenShinGothic-Bold.ttf"))

    warningMap = Image.open(f'{dirName}/warningMap.png')
    warningMap = warningMap.crop((500, 0, 1900, 2400))
    warningMap = warningMap.resize((630, 1080))

    BaseBG.paste(warningMap)
    fontGSG_B40 = ImageFont.truetype(fontpathGSG_B, 40)
    fontGSG_B50 = ImageFont.truetype(fontpathGSG_B, 50)

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
        for wCode in cityWarningData[cWD]:
            if int(wCode) >= 32:
                boxFillColor = "#7030a0"
            elif int(wCode) <= 10:
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