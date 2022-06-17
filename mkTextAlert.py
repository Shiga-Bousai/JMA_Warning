from PIL import Image, ImageDraw, ImageFont #pip install pillow-simd

from os.path import dirname, abspath, join
dirName = dirname(abspath(__file__))

imageBaseColor = "#313131"

fontpathGSG_B = join(dirName,abspath("../fonts/BIZ-UDGothicB.ttc"))
fontGSG_B30 = ImageFont.truetype(fontpathGSG_B, 30)
fontGSG_B60 = ImageFont.truetype(fontpathGSG_B, 60)

def main(
  outpputFile=f'{dirName}/output.jpeg',
  headerText='',
  mainText='',
  mainBaseColor='#121212',
  mainTextColor='#fcfefd',
  headerBaseColor='#952091',
  headerTextColor='#fcfefd',
  icon=None
):
  #Base生成
  BaseBG = Image.new('RGB', (1280, 10000), mainBaseColor)  # 下地となるイメージオブジェクトの生成
  draw = ImageDraw.Draw(BaseBG)  # drawオブジェクトを生成

  baseTop = 190
  baseLeft = 50

  draw.rectangle((0, 0, 1280, 120), fill=headerBaseColor)
  headerTextBox = draw.multiline_textbbox((0,0), headerText, font=fontGSG_B60)
  headerTextW = headerTextBox[2] - headerTextBox[0]
  headerTextH = headerTextBox[3] - headerTextBox[1]
  print(headerTextW,headerTextH)
  draw.multiline_text(
    (
      (1280 - headerTextW) / 2,
      (120 - headerTextH) / 2
    ),
    headerText,
    font=fontGSG_B60,
    fill=headerTextColor
  )


  #改行ごとにarray化
  mainText = mainText.split('\n')
  #一文字ごとに描画する
  for mainTextArr in mainText:
      for hl_text in mainTextArr:
          textBox = draw.multiline_textbbox((0,0), hl_text, font=fontGSG_B30)
          textW = textBox[2] - textBox[0]
          if baseLeft + textW > 1230:
              baseTop += 50
              baseLeft = 50
          draw.multiline_text((baseLeft,baseTop), hl_text, font=fontGSG_B30,fill='#efefef',anchor='lm')
          baseLeft += textW
      baseTop += 50
      baseLeft = 100
  baseTop += 10

  if baseTop + 50 < 720:
    baseTop = 720
  BaseBG = BaseBG.crop((0, 0, 1280, baseTop + 50))

  #画像の保存
  wImagePath = f'{outpputFile}'
  BaseBG.save(wImagePath)

if __name__ == '__main__':
  main()