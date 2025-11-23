from datetime import datetime
import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed
import os, sys
sys.path.append(os.path.abspath("./src")) 
from meituan import MeituanService

year, month = 2025, 8
days = calendar.monthrange(year, month)[1]

# 1️⃣ 创建对象
objs = [MeituanService(datetime(year, month, d)) for d in range(1, days + 1)]

# 2️⃣ 并发获取每一天的 discount_price_sum
with ThreadPoolExecutor(max_workers=16) as executor:
    futures = [executor.submit(obj.get_discount_sum) for obj in objs]
    for future in as_completed(futures):
        future.result()  # 等待完成，若抛异常会在这里抛出

# 3️⃣ 汇总
total_sum = sum(obj.discount_price_sum for obj in objs)
print("总折扣金额:", total_sum)uv 
