import sys
import os
sys.path.append(os.path.abspath("./src"))

from operation import OperationService
from meituan import MeituanService
from douyin import DouyinService

from datetime import datetime, timedelta
# date=datetime(2025,10,16)
date = datetime.now()-timedelta(days=1)

op =  OperationService(date)
mt = MeituanService(date)
dy = DouyinService(date)
#这个地方，业务逻辑应该是，必须有值，否则报空值异常
sum = dy.data.get('douyin_total', 0) + mt.data.get('meituan_total', 0) + op.data.get('turnoverSumFee', 0)
sum = round(sum, 2)
print(sum)