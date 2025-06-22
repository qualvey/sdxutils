
from tools import iheader, env, logger
from typing import List
from datetime import timedelta, datetime
import urllib.parse
import requests
import json

logger = logger.get_logger(__name__)

def get_previous_week_range(dt: datetime) -> List[datetime]:
    # 计算当前日期是星期几，星期一为0，星期日为6
    current_weekday = dt.weekday()
    # 计算上周日距离当前日期的天数
    days_since_last_sunday = current_weekday + 1
    # 计算上周日的日期
    last_sunday = dt - timedelta(days=days_since_last_sunday)
    # 计算上周一的日期
    last_monday = last_sunday - timedelta(days=6)
    week_dates = [last_monday + timedelta(days=i) for i in range(7)]
    return week_dates


def get_data_aday(date_str: str):
    url_dict = {
    "scheme": "https",
    "host": "hub.sdxnetcafe.com",
    "filename": "/api/statistics/branch/operation/data/info",
    "query": {
        "branchId": "a92fd8a33b7811ea87766c92bf5c82be",
        "startTm": date_str
        }
    }

    scheme = url_dict.get("scheme", "")
    host = url_dict.get("host", "")
    filename = url_dict.get("filename", "")
    query = url_dict.get("query", {})
    query_string = urllib.parse.urlencode(query)
    url = urllib.parse.urlunparse((scheme, host, filename, '', query_string, ''))
    response  = requests.get(url, headers=iheader.headers)
    return response.json()

def get_sum(date_list: List[datetime]) -> int:
    value = 0
    for date_items in date_list:
        date_str = str(date_items)
        data     = get_data_aday(date_str)
        num = round(data['data']['duration']/60, 2)
        value +=  num
    return value

    with open(f"{env.proj_dir}/worktime/data.info.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

date_list = get_previous_week_range(datetime.today())
logger.info(f'start date{date_list[0]}')
#print('datelist元素的数据类型',date_list[0].__class__)

if __name__ == "__main__":
    value = get_sum(date_list)
    logger.info(f"{value}")
