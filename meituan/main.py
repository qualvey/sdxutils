import requests
import json
from datetime import datetime, timedelta, date
import pytz
import argparse

from tools import env, logger
from urllib.parse import unquote

#loger = logger.get_logger(name='meituan', log_file=f'{env.proj_dir}/meituan/log')
logger = logger.get_logger(__name__)

cookies_str  = env.configjson['cookies']['mt']
proj_dir = env.proj_dir

mt_status   = 0
mt_api = "https://e.dianping.com/couponrecord/queryCouponRecordDetails"

common_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh,en-US;q=0.7,en;q=0.3",
    "Content-Type": "application/json",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
}

headers = {
    **common_headers,
    "Origin": "https://e.dianping.com",
    "Referer": "https://e.dianping.com/app/np-mer-voucher-web-static/records"
}
        

def parse_cookies(cookie_str):
    cookies = dict(item.strip().split("=", 1) for item in cookie_str.split("; ") if "=" in item)
    return cookies

cookies = parse_cookies(cookies_str)

def get_meituanSum(date):
    #date: <datetime.datetime>对象
    today_start = datetime(date.year, date.month, date.day)
    today_end = today_start + timedelta(hours=23, minutes=59, seconds=59)
    logger.info(f'美团数据日期{today_end.month}')
    # 转换为 Unix 时间戳（单位：秒）
    begin_timestamp = int(today_start.timestamp()*1000)
    end_timestamp = int(today_end.timestamp()*1000)

    data = {
        "selectDealId": 0,
        "bussinessType": 0,
        "selectShopId": 1340799757,
        "productTabNum": 1,
        "offset": 0,
        "limit": 100,
        "beginDate": begin_timestamp,
        "endDate": end_timestamp,
        "subTabNum": None
    }

    try:
        response = requests.post(url = mt_api,  headers=headers, json=data, cookies=cookies)
        #response = requests.post(url = mt_api, params=params, headers=headers, json=data, cookies=cookies)
        response.raise_for_status()  # HTTP 错误（4xx/5xx）抛出异常

        try:
            json_data = response.json()
            with open(f"{proj_dir}/meituan/meituan.json",'w') as data_json:
                json.dump(json_data, data_json, ensure_ascii=False, indent=4)
        except json.JSONDecodeError:
            print("响应不是合法 JSON")
            json_data = None
    except RequestException as e:
        print(f"请求失败: {e}")
        json_data = None

    sale_price_sum = 0
    couponRecordDetails = json_data["data"]["couponRecordDetails"]
    mt_len              = json_data['data']['recordSum']

    if  couponRecordDetails:           
        i=0
        logger.info('美团列表')
        for record in couponRecordDetails:
            price = record["salePrice"]
            logger.info(f'{price}\t')
            sale_price = price.replace("¥", "")       # 去除货币符号
            sale_price_sum += float(sale_price)
            sale_price_sum = round(sale_price_sum, 2) 
            i+=1
        logger.info(f'总计{i}单')
    return sale_price_sum, mt_len

def get_mtgood_rates(date):

    '''
        date<str>
        query time range<string %Y-%mp-%d>
    '''

    url_comment = "https://e.dianping.com/review/app/index/ajax/pcreview/listV2"
    query    = {
        "platform": "1",
        "shopIdStr": "1340799757",
        "tagId": "1",
        "startDate": date,
        "endDate": date,
        "pageNo": "1",
        "pageSize": "20",
        "referType": "0",
        "category": "0",
        "yodaReady": "h5",
        "csecplatform": "4",
        "csecversion": "3.1.0",
        "mtgsig": "{\"a1\":\"1.2\",\"a2\":1744742288824,\"a3\":\"1740084568043CAMCCCC2960edaad10e294fa6f28397fe2285903389\",\"a5\":\"0Gj96O8oa4QSDdx7vLmthAfRTKAsrA739yHO+2oNMQ+qe40zyFH=\",\"a6\":\"hs1.6bdBbku5qBC9y8yYYsjGEJJyStbDulDRGAcHdVhidjC5Wa3kcaa5bio2L+EktgYXQpUI9r7xs1YaEsFME60N3kIQY7nNxQNCThkddZLuAIIsZUZjXUkbXBJ5UI4+OsO9a\",\"a8\":\"d5f8e4bebeaa405401d4eae22514af44\",\"a9\":\"3.1.0,7,209\",\"a10\":\"0c\",\"x0\":4,\"d1\":\"8d7b1e4070d501d7382a8b49fdae1f9c\"}"
    }

    headers_comment = {
        **common_headers,
        "Host": "e.dianping.com",
        "Pragma": "no-cache",
        "Referer": "https://e.dianping.com/vg-platform-reviewmanage/shop-comment-mt/index.html"
        
    }
    response = requests.get(url=url_comment, params = query, cookies = cookies ,headers = headers_comment)
    data_json = response.json()
    high_rates = data_json['msg']['totalReivewNum']
    return high_rates
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="美团组件")
    parser.add_argument("-n", "--now", action="store_true", help="今天的数据")
    parser.add_argument("-d", "--date", type=str, help="今天的数据")
    args = parser.parse_args()
    if args.date:
        working_date = args.date
        date_obj = datetime.strptime(working_date, "%Y-%m-%d")
        logger.info(f"美团日期{working_date}")
        mtsum, mtlen = get_meituanSum(date_obj)
        logger.info(f'美团数据: {mtsum}')
        googs_rates = get_mtgood_rates(working_date)
        logger.info(f'美团改日好评数量{googs_rates}')
        get_mtgood_rates(date_obj)
    elif args.now:
        working_date =  datetime.today()
        logger.info(f"美团日期{working_date}")
        mtsum, mtlen = get_meituanSum(working_date)
        logger.info(f'美团数据: {mtsum}')
        googs_rates = get_mtgood_rates(working_date)
        logger.info(f'美团改日好评数量{googs_rates}')
        get_mtgood_rates(working_date)
    else:
        yesterday =datetime.today()-timedelta(days=1) 
        mtsum = get_meituanSum(yesterday)
        logger.info(f'美团数据{yesterday}: {mtsum}')
        get_mtgood_rates(yesterday)

