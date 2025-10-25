import sys,os , threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime, timedelta
sys.path.append(os.path.abspath("./src"))

from operation import OperationService
from meituan import MeituanService
from douyin import DouyinService

# date=datetime(2025,10,16)
#date = datetime.now()-timedelta(days=1)
date = datetime.now()

def opworker():
    op =  OperationService(date)
    return op.data.get('turnoverSumFee')
def mtworker():
    mt = MeituanService(date)
    return mt.data.get('meituan_total')
def dyworker():
    dy = DouyinService(date)
    return dy.data.get('douyin_total')

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(opworker): "op",
        executor.submit(mtworker): "mt",
        executor.submit(dyworker): "dy",
    }

    results = {}
    sum = 0
    for future in as_completed(futures):
        name = futures[future]
        sum += future.result()
        results[name] = future.result()

print(results)
#这个地方，业务逻辑应该是，必须有值，否则报空值异常
#sum = dy.data.get('douyin_total', 0) + mt.data.get('meituan_total', 0) + op.data.get('turnoverSumFee', 0)
#sum = round(sum, 2)
print(f"总营业额:{sum}")
