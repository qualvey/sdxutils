import sys
import os
sys.path.append(os.path.abspath("/Users/ryu/code/sdxutils/src"))
# sys.path.append(os.path.abspath("../src"))  # 临时加入 src 目录到 sys.path
from specialFee import SpecialFee
from datetime import datetime
date=datetime(2025,10,16)
sf = SpecialFee(date)
print(sf.data)

known_data = {
    'detail': {
        '客情维护': 300, 
        '抖音团购': 600, 
        '美团团购': 1100,
        '股东赠送': 500,
        '员工网费': 627,
        '游戏奖励': 10
        }, 
    'sum': 3137}
def test_special_fee_service():
    date = datetime(2025, 10, 16)
    sf_service = SpecialFee(date)
    
    assert 'detail' in sf_service.data, "detail not in data"
    assert 'sum' in sf_service.data, "sum not in data"
    
    detail = sf_service.data['detail']
    total_sum = sf_service.data['sum']
    
    assert detail == known_data['detail'], f"detail does not match. Expected: {known_data['detail']}, Got: {detail}"
    assert total_sum == known_data['sum'], f"sum does not match. Expected: {known_data['sum']}, Got: {total_sum}"
