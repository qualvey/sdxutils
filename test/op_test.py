import sys
import os
sys.path.append(os.path.abspath("./src"))

# sys.path.append(os.path.abspath("../src"))  # 临时加入 src 目录到 sys.path
#总金额是data.turnoverSumFee
from operation import OperationService
from datetime import datetime
date=datetime(2025,10,16)

op =  OperationService(date)
print(op.data)
def test_operation_service():
    date = datetime(2025, 10, 16)
    op_service = OperationService(date)
    
    assert 'turnoverSumFee' in op_service.data, "turnoverSumFee not in data"
    
    turnover_sum_fee = op_service.data['turnoverSumFee']
    
    # assert isinstance(turnover_sum_fee, int), "turnoverSumFee is not an integer"
    # assert isinstance(order_count, int), "orderCount is not an integer"
    
    assert turnover_sum_fee == 2780.9, "turnoverSumFee is negative"
    # assert turnover_sum_fee >= 0, "turnoverSumFee is negative"