import requests
import json
from datetime import datetime, timedelta
import argparse

import time
from tools import env
from tools.logger import get_logger

logger = get_logger(__name__)

cookie          = env.configjson['cookies']['dy']

common_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh,en-US;q=0.7,en;q=0.3",
        "Content-Type": "application/json",
        "Agw-Js-Conv": "str",
        "x-tt-trace-log": "01",
        "Ac-Tag": "smb_s",
        "rpc-persist-life-merchant-role": "0",
        "rpc-persist-life-merchant-switch-role": "1",
        "rpc-persist-life-biz-view-id": "0",
        "rpc-persist-lite-app-id": "100281",
        "rpc-persist-life-platform": "pc",
        "rpc-persist-terminal-type": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0"
}
specific_headers = {
        "x-tt-trace-id": "00-833c459518ddb35cb728491cb-833c459518ddb35c-01",
        "rpc-persist-session-id": "100281b8-90cf-4fe7-acdc-4568a43d7667",
        "x-secsdk-csrf-token": "000100000001ca5a6af103350fc8059c84b0e50942e3f3a8686a721e2fdce8ba3cb75158d32118377800f3fe4702",
        "x-tt-ls-session-id": "670c204f-500f-41dc-8123-51da77a17d0e",
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    }

headers = common_headers | specific_headers

def fetch_douyin_data(date,max_retries=5, delay=2):
    '''
    date<datetime.date>
    '''
    url = "https://life.douyin.com/life/trade_view/v1/verify/verify_record_list/"
    
    params  = {
        'page_index': 1,
        'page_size' : 100,
        'industry'  : 'industry_common', 
        'root_life_account_id' : '7143570945559037956'
    }
    logger.info(f'抖音日期:{date}')

    time_start = datetime(date.year, date.month, date.day)
    time_end = time_start + timedelta(hours=23, minutes=59, seconds=59)

    # 转换为 Unix 时间戳（单位：秒）
    # datetime对象有timestamp方法
    begin_timestamp = int(time_start.timestamp())
    end_timestamp = int(time_end.timestamp())

    post_data = {
        "filter":{
            "start_time": begin_timestamp,
            "end_time": end_timestamp,
            "poi_id_list":[],
            "sku_id_list":[],
            "product_option":[],
            "is_market":False,
            "is_market_poi":False
        },
        "is_user_poi_filter":False,
        "is_expend_to_poi":True,
        "auth_poi_extra_filter":{},
        "industry":"industry_common",
        "permission_common_param":{}
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(url, params=params, json=post_data, headers=headers, cookies=cookie)
            response.raise_for_status()  # 如果状态码不是 200，抛出异常
            douyin_json = response.json()
            if douyin_json:
                logger.info("获取抖音数据成功.")
                logger.debug(f'详细原始json:{json.dumps(douyin_json, indent=4, ensure_ascii=False)}')

            with open(f"{env.proj_dir}/douyin/douyin.json", 'w', encoding='utf-8') as data_json:
                json.dump(douyin_json, data_json, ensure_ascii=False, indent=4)

            return douyin_json  # 请求成功，返回 JSON 数据
        
        except requests.exceptions.RequestException as e:
            logger.error(f"请求发生错误（第 {attempt+1} 次尝试）：{e}")

            if attempt < max_retries - 1:  # 如果还有重试机会，等待后重试
                time.sleep(delay)  # 等待 delay 秒后重试
            else:
                logger.error("抖音已达到最大重试次数，放弃请求")
                return None  # 所有尝试都失败，返回 None

def get_douyin_data(date):
    '''
    date<datetime.date>
    '''
    sum = 0
    douyin_json = fetch_douyin_data(date)
    try:
        dy_list = douyin_json.get('data').get('list')
        if dy_list:
            dy_len  = len(dy_list)
            logger.info("抖音列表")
            for item in dy_list:
                verify_amount = item['amount']['verify_amount']
                logger.info(verify_amount/100)
                sum += verify_amount/100
        else:
            dy_len  = 0
    except KeyError as e:
        breakpoint()
        logger.error(f'返回中不存在期待的键，报错。{e}')
        return None, None

    if sum==0:
        return None, 0
    else:
        return sum, dy_len

def get_dygood_rate(date):

    date_start = datetime(date.year, date.month, date.day)
    date_end = date_start + timedelta(hours=23, minutes=59, seconds=59)

    # 转换为 Unix 时间戳（单位：秒）
    # datetime对象有timestamp方法
    begin_timestamp = int(date_start.timestamp())
    end_timestamp   = int(date_end.timestamp())

    url      = "https://life.douyin.com/life/infra/v1/review/get_review_list/"
    
   #几个id可能会改变 
    query  = {
        "life_account_ids": "7494586712149051455",
        "life_account_id": "7143570945559037956",
        "root_life_account_id": "7143570945559037956",
        "poi_id": "6828149180763080708",
        "tags": "1,9,5,4,10,8,7,50,",
        "sort_by": "2",
        "query_time_start": begin_timestamp,
        "query_time_end": end_timestamp,
        "search_after": "",
        "cursor": "0",
        "count": "10",
        "top_rate_ids": "",
        "reply_display_by_level": "1",
        "store_type": "2",
        "source": "1"
        }

    response = requests.get(
        url = url ,
        params = query,
        headers = headers,
        cookies = cookie
        )

    data = response.json()
    response_list = data.get('data').get('reviews')
    logger.debug('get_good_rate:\n')
    logger.debug(json.dumps(response_list, indent = 4, ensure_ascii=False))
    if response_list is not None:
        list_len = len(response_list)
        return list_len
    else:
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抖音模块")
    parser.add_argument("-n", "--now",  action = "store_true", help="今天")
    parser.add_argument("-d", "--date", type=str, help="指定日期")
    args = parser.parse_args()
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d")
        logger.info(f'date: {date}')
        sum, len_of_list = get_douyin_data(date)
        good_rates = get_dygood_rate(date)
        logger.info(f'好评数量：{good_rates}')
    if args.now:
        date = datetime.today()
        logger.info(f'date: {date}')
        sum, len_of_list = get_douyin_data(date)
        good_rates = get_dygood_rate(date)
        logger.info(f'好评数量：{good_rates}')
    else:
        sum, len_of_list =    get_douyin_data(datetime.today() - timedelta(days=1))
    logger.info(f"抖音总金额: {sum}")

