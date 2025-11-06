import sys
import os
sys.path.append(os.path.abspath("../src"))
# sys.path.append(os.path.abspath("../src"))  # 临时加入 src 目录到 sys.path

from meituan import MeituanService
from datetime import datetime
date=datetime(2025,10,16)

mt = MeituanService(date)
mt.data.get('meituan_total')
mt.data.get('mt_count')
print(mt.data)
def test_meituan_service():
    date = datetime(2025, 10, 16)
    mt_service = MeituanService(date)
    
    assert 'meituan_total' in mt_service.data, "meituan_total not in data"
    assert 'mt_count' in mt_service.data, "meituan_count not in data"
    
    meituan_total = mt_service.data['meituan_total']
    meituan_count = mt_service.data['mt_count']
    
    # assert isinstance(meituan_total, int), "meituan_total is not an integer"
    # assert isinstance(meituan_count, int), "mt_count is not an integer"
    
    assert meituan_total >= 0, "meituan_total is negative"
    assert meituan_count >= 0, "mt_count is negative"
