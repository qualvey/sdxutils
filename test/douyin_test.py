import sys,os

sys.path.append(os.path.abspath("./src"))
#json{'douyin_total': 146.3, 'dy_count': 7, 'dy_good': 0}
# sys.path.append(os.path.abspath("../src"))  # 临时加入 src 目录到 sys.path
from douyin import DouyinService
from datetime import datetime
date=datetime(2025,10,16)
dy = DouyinService(date)
print(dy.data)
def test_douyin_service():
    date = datetime(2025, 10, 16)
    dy_service = DouyinService(date)
    
    assert 'douyin_total' in dy_service.data, "douyin_total not in data"
    assert 'dy_count' in dy_service.data, "dy_count not in data"
    
    douyin_total = dy_service.data['douyin_total']
    dy_count = dy_service.data['dy_count']
    
    # assert isinstance(douyin_total, int), "douyin_total is not an integer"
    # assert isinstance(dy_count, int), "dy_count is not an integer"
    
    assert douyin_total >= 0, "douyin_total is negative"
    assert dy_count >= 0, "dy_count is negative"
