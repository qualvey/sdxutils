from tools import iheader
import requests
from datetime import datetime, timedelta
import json
from tools import logger as mylogger
from collections import defaultdict
from typing import List, Dict
from wcwidth import wcswidth

headers = iheader.headers
logger  = mylogger.get_logger(__name__)

def get_consume(certId: str) -> dict:

    endTime = datetime.now().strftime('%Y-%m-%d') + ' 23:59:59'
    start_dt = datetime.now() - timedelta(days=60)
    startTime = start_dt.strftime('%Y-%m-%d') + ' 00:00:00'
    api = "https://hub.sdxnetcafe.com/api/payment/order/list/page"
    params = {
    "orderType":"SALE",
    "cardId" : certId ,
    "startTm": startTime,
    "endTm"  : endTime,
    "page"    : 1,
    "limit"   : 100,
    "branchId": "a92fd8a33b7811ea87766c92bf5c82be",
    "sortName": "createdTime",
    "sortOrder":"desc"
    }

    logger.debug(f"请求参数:\n{json.dumps(params, ensure_ascii=False, indent=4)}")
    response = requests.get(url = api, params=params, headers=headers)
    return response.json()

def get_product_totals(data: List[dict]) -> Dict[str, float]:
    product_total = defaultdict(float)
    total = 0.0

    for item in data:
        status = item.get("status")
        paid = item.get("paid")
        amount = item.get("finalAmount", 0)
        name = item.get("productNameQuantity")

        # 统一判断条件
        if status == "COMPLETED" and paid is True and amount != 0 and name is not None:
            product_total[name] += amount
            total += amount

    product_total['sum'] = total
    return dict(product_total)

def pretty_align_dict(data: Dict[str, float]) -> str:
    """
    接收 dict[str, float]，返回一个字符串，
    键左对齐（支持中文宽度），值右对齐两位小数。
    """
    if not data:
        return ""

    max_key_len = max(wcswidth(k) for k in data)

    lines = []
    for k, v in data.items():
        padding = max_key_len - wcswidth(k)
        line = f"{k}{' ' * padding} : {v:>6.2f}"
        lines.append(line)

    return "\n".join(lines)

def get_consume_list(certId: str) -> str:
    result = get_consume(certId)
    result = result.get('data').get('rows')
    details: dict[str, float] = get_product_totals(result)
    fdetails = pretty_align_dict(details)

    return fdetails

if __name__ == "__main__":

    id = "340202199901220012"

    result = get_consume(id)
    with open('./consume.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    result = result.get('data').get('rows')

    details: dict[str, float] = get_product_totals(result)
    fdetails = pretty_align_dict(details)

    logger.info(f"\n{fdetails}\n")
