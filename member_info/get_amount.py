import requests
import json
import argparse
from tools import iheader
from tools import logger as mylogger
from datetime import datetime

headers  = iheader.headers
logger  = mylogger.get_logger(__name__)

parser = argparse.ArgumentParser(description="用户充值统计工具")
parser.add_argument('id',              type=str, help='身份证号')
parser.add_argument('-id', '--cardid', type=str, default=None, help='身份证号码')
args = parser.parse_args()

url =  "https://hub.sdxnetcafe.com/api/member/member/balance/alteration"

# 获取今天日期并格式化为 yyyy-mm-dd+23:59:59

starttime = "2019-01-01+00:00:00"
endTime = datetime.now().strftime('%Y-%m-%d') + '+23:59:59'

def get_total_amount(id:str) -> int | float:

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

    with open("./member.json", "w",  encoding = "utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=4)
    
    total_amount = sum(
        row["amount"]
        for row in info["data"]["rows"]
        if row.get("consumeType") == "充值本金"
    )
    return total_amount

if __name__ == "__main__":
    card_id = args.cardid or args.id  # 只要有一个就用，没有就为 None

    # 如果两个都存在且值不同，记录警告或提示
    if args.cardid and args.id and args.cardid != args.id:
        logger.warning(f"参数 cardid 和 id 都提供了，但值不同，将优先使用 cardid={args.cardid}")

    if card_id:
        amount = get_total_amount(card_id)
        msg = f"总的充值金额 {amount}"
        logger.info(msg)
