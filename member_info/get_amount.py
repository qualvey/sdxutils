import requests
import json
import argparse
from tools import iheader
from datetime import datetime
from typing import List, Dict

headers  = iheader.headers

from tools import logger as mylogger
logger  = mylogger.get_logger(__name__)


def get_total_amount(id:str) -> dict[str,  float | str]:
    info ={}

    starttime = "2019-01-01+00:00:00"
    endTime = datetime.now().strftime('%Y-%m-%d') + '+23:59:59'
    url =  "https://hub.sdxnetcafe.com/api/member/member/balance/alteration"

    params = {
    "cardId"    : id,
    "startTm"   : starttime,
    "endTm"     : endTime,
    "page"      : 1,
    "limit"     : 999999,
    "branchId"  : "a92fd8a33b7811ea87766c92bf5c82be",
    "sortName"  : "createdTime",
    "sortOrder" : "desc"
    }
    response = requests.get(url = url, params = params, headers=headers)
    info  = response.json()

    with open("./amount.json", "w",  encoding = "utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=4)
    
    total_amount = sum(
        row["amount"]
        for row in info["data"]["rows"]
        if row.get("consumeType") == "充值本金"
    )
    rows = info.get('data', {}).get('rows', [])
    if rows:
        oldestTime = rows[-1].get('createdTime')
    else:
        oldestTime = "没有消费历史"  # 或者你可以设置为一个默认时间，比如 0 或 ''
    info['total_amount']  = total_amount
    info['first_paid_date']  = oldestTime
    return info

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="用户充值统计工具")
    parser.add_argument('id',              type=str, help='身份证号')
    parser.add_argument('-id', '--cardid', type=str, default=None, help='身份证号码')
    args = parser.parse_args()

    card_id = args.cardid or args.id  # 只要有一个就用，没有就为 None

    # 如果两个都存在且值不同，记录警告或提示
    if args.cardid and args.id and args.cardid != args.id:
        logger.warning(f"参数 cardid 和 id 都提供了，但值不同，将优先使用 cardid={args.cardid}")

    if card_id:
        amount = get_total_amount(card_id)
        msg = f"总的充值金额 {amount}"
        logger.info(msg)
