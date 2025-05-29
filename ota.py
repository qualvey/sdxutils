import meituan.main as mt
import douyin.main as dy
import json
from datetime import date, datetime, timedelta
from operation.main import today_income
from operation import ThirdParty
from tools.logger import get_logger

import schedule
import time
import argparse
import logging

logger =  get_logger(__name__)
levelNum = logger.getEffectiveLevel()
level = logging.getLevelName(levelNum)
logger.info(f'log Level: {level}')
# 获取今天的日期
today = date.today()
today_datetime=datetime.combine(today, datetime.min.time())
logger.info(f'今天的日期:{today}')

douyin_sum , _ = dy.get_douyin_data(today)
meituan_sum, _ = mt.get_meituanSum(today)

ota_info ={
    'DOUYIN'  : meituan_sum,
    'MEITUAN' : douyin_sum
}
income         = today_income(today)

income_dict = {'MEITUAN': meituan_sum, 'DOUYIN':douyin_sum}

ota_update  = ThirdParty.ota_update
delete_third = ThirdParty.delete
check_unique = ThirdParty.check_unique

def update(date):
    names = ['MEITUAN', 'DOUYIN']

    logger.info('updating ota infomation')
    ids = check_unique(str(date))

    date_datetime=datetime.combine(date, datetime.min.time())
    logger.debug(f'三方已经存在的数据{ids}')
    status =[]
    for type, id_list in ids.items():
        obj = {}
        delete_status_list = []
        for id in id_list:
            delete_status = delete_third(id)
            delete_status_list.append(delete_status)
        obj['type']     = type
        obj['status']   = delete_status_list
        status.append(obj)
        new_create = []
    # 提取 b 中所有 name 字段的值
    names_in_b = {item['type'] for item in status}
    # 判断 a 中的每个元素是否都出现在 b 的 name 列表中
    #result = all(name in names_in_b for name in names)
    missing = [name for name in names if name not in names_in_b]

    if status:
        for  i in status:
            if 1 in i['status']:
                logger.error(f'delete 存在失败{status}')
            else:
                ota_update(ota_name=i['type'], date_obj=date_datetime, income=income_dict[i['type']])
            for name in names:
                if name == i['type']:
                    flag_in = True
                else:
                    flag_in = False
    else:
        ota_update('MEITUAN', date_datetime, meituan_sum)
        ota_update('DOUYIN', date_datetime, douyin_sum)

    if missing:
        for missing_name in missing:
            logger.info(f'{missing_name} is new .')
            ota_update(missing_name, date_datetime, ota_info[missing_name])

def run(date):

    ota_sum = (douyin_sum or 0) + (meituan_sum or 0)
    data = {
        "抖音收入": round(douyin_sum or 0, 2),
        "美团收入": round(meituan_sum or 0, 2),
        "OTA收入合计": round(ota_sum, 2),
        "收银台收入": round(income or 0, 2),
        "今日总营业额": round(ota_sum + (income or 0), 2)
    }
    max_key_len = max(len(k) for k in data.keys())

    lines = ["{"]
    for key, value in data.items():
        lines.append(f'  "{key:<{max_key_len}}": {value:>6.2f},')
    lines[-1] = lines[-1].rstrip(',')  # 去掉最后一行的逗号
    lines.append("}")

    formatted_result = "\n".join(lines)
    logger.info(formatted_result)
    update(date)
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="收入计算")
    parser.add_argument("-n", "--now", action="store_true", help="启用调试模式")
    parser.add_argument("-d", "--date", type=str, help="指定日期")
    args = parser.parse_args()
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d")
        logger.info(f'date: {date}')
    else:
        date = today

    run(date)
