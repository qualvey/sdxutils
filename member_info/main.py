import json
import argparse
from member_info  import get_amount, get_cardid, get_consume

from tools import logger as mylogger

logger  = mylogger.get_logger(__name__)

def get_detail(name : str) -> list[dict]:
    result = get_cardid.get_person_info(name)

    for member in result:

        id = member.get('certId')
        consume_str = get_consume.get_consume_list(id)
        amount_info = get_amount.get_total_amount(id)
        member['总充值']  = amount_info['total_amount']
        member['第一次充值'] = amount_info['first_paid_date']
        member['_consume_str'] = consume_str  # 临时字段，仅用于日志打印

    return result

def print_detail(result: list[dict]):
    for i, member in enumerate(result, 1):
        # 复制一个不含 _consume_str 的副本
        safe_member = {k: v for k, v in member.items() if k != '_consume_str'}
        
        # 打印 member 信息
        json_str = json.dumps(safe_member, ensure_ascii=False, indent=4)
        logger.info(f"\n {member.get('realName')} ：\n{json_str}")
        
        # 单独打印消费记录（格式化过）
        logger.info(f"近两月消费历史：\n{member['_consume_str']}")

#breakpoint()
if __name__  == "__main__":
    parser = argparse.ArgumentParser(description="获取用户信息")
    parser.add_argument('name',              type=str, help='姓名')
    parser.add_argument('-n', '--name', type=str, default=None, help='姓名')
    args = parser.parse_args()

    name = args.name
    result = get_detail(name)
    print_detail(result)

    #str_json = json.dumps(result, ensure_ascii=False, indent=4)
    #logger.info(str_json)
