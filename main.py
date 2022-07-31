from warning import getWarning
from os import remove
from datetime import datetime, timezone, timedelta
from os.path import dirname, abspath
import sys

now = datetime.now(timezone(timedelta(hours=9)))
dirName = dirname(abspath(__file__))
args = sys.argv

# 時刻周りの生成
# now : 現在時刻
# jmaLastUpdate : 前回のアップデート
with open(f"{dirName}/tmp.txt") as f:
    jmaLastUpdate = f.read()
    jmaLastUpdate = jmaLastUpdate.replace("\n", "").replace(" ", "")
    if jmaLastUpdate != "":
        jmaLastUpdateDatetime = datetime.strptime(jmaLastUpdate, "%Y-%m-%dT%H:%M:%S%z")
    else:
        jmaLastUpdateDatetime = now + timedelta(minutes=-5)

updatedDatetime = getWarning(jmaLastUpdateDatetime, args)

# 気象庁のアップデート時間の更新(更新の有無に関わらず)
with open(f"{dirName}/tmp.txt", mode="w") as f:
    if updatedDatetime == None:
        f.write(jmaLastUpdate)
    else:
        f.write(updatedDatetime)
