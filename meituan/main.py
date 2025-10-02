

from datetime import datetime, timedelta

import argparse, os, sys, json, requests

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QThread, Signal
from typing import Optional, Dict, Any, Tuple

from tools import env
from tools import logger as mylogger
from typing import Any, Dict, Tuple, Optional
from requests.exceptions import RequestException

logger = mylogger.get_logger(__name__)

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

#要想办法判断cookie是否失效
def parse_cookies(cookie_str):
    cookies = dict(item.strip().split("=", 1) for item in cookie_str.split("; ") if "=" in item)
    return cookies

cookies = parse_cookies(cookies_str)

# https://e.dianping.com/review/app/index/ajax/pcreview/listV2?platform=1
# shopIdStr=1340799757
# tagId=1
# startDate=2025-09-30
# endDate=2025-09-30
# pageNo=1
# pageSize=10
# referType=0
# category=0
# yodaReady=h5
# secpltform=4
# csecversion=4.0.4
# mtgsig=%7B%22a1%22%3A%221.2%22%2C%22a2%22%3A1759267349750%2C%22a3%22%3A%221758131109387IKYIQGEfd79fef3d01d5e9aadc18ccd4d0c95072322%22%2C%22a5%22%3A%22ZBfDwtpBGm%2F4861YBNXYOb9mq2jM67slNpkwsyYQvMEv4i0pRkAdYL%2Faq%2ByY3D3YoxWPL9Jr9a6CLB3E92ADGkRpDI%3D%3D%22%2C%22a6%22%3A%22hs1.6L0z6EnhuTEwFP0z8lbe5KAB4hoOQPGpFzKfoc%2B%2BlOA8A5EuPyOWvi2SUzNZqSofxso8gn3E49lCDQV73NVvrg6KsbCuuwQDbtHc7L4oF6ozsxnxgTo7dPlc9LxYaYK1i%22%2C%22a8%22%3A%2229597c60f176e49f8ccca3345445f252%22%2C%22a9%22%3A%224.0.4%2C7%2C94%22%2C%22a10%22%3A%2267%22%2C%22x0%22%3A4%2C%22d1%22%3A%22f66d474c144fa9e1a5af8b0fe222eea0%22%7D

class MeituanService():
    """
        {mt_total: float, mt_count: int, mt_good: int}
"""     
    def __init__(self,date: datetime):
        self.date = date
        self.data = {}
        self.get_meituan_sum()
        self.get_good_num()

    def get_meituan_sum(self) -> Tuple[float, int]:
        """和之前同步版本逻辑一样，只是没有 GUI 阻塞，出错抛异常"""
        today_start = datetime(self.date.year, self.date.month,self.date.day)
        today_end = today_start + timedelta(hours=23, minutes=59, seconds=59)
        logger.info(f'美团数据日期 {today_start.strftime("%Y-%m-%d")}')

        begin_timestamp = int(today_start.timestamp() * 1000)
        end_timestamp = int(today_end.timestamp() * 1000)

        request_data = {
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

        sale_price_sum = 0.0
        mt_len = 0

        response = requests.post(url=mt_api, headers=headers, json=request_data, cookies=cookies)
        response.raise_for_status()
        json_data = response.json()
        if not json_data:
            raise ValueError("美团请求返回空值，请检查 cookie 是否失效")

        # 保存 JSON 响应
        os.makedirs(f"{proj_dir}/meituan", exist_ok=True)
        print('ksjdkasjdlksaj')
        with open(f"{proj_dir}/meituan/meituan.json", 'w', encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        data = json_data.get("data", {})
        coupon_records = data.get("couponRecordDetails", [])
        mt_len = data.get("recordSum", 0)

        for record in coupon_records:
            price_str = record.get("salePrice", "")
            try:
                sale_price = float(price_str.replace("¥", "").strip())
                sale_price_sum += sale_price
            except ValueError:
                logger.warning(f"无法解析价格: {price_str}")
        sale_price_sum = round(sale_price_sum, 2)
        self.data['meituan_total'] = sale_price_sum
        self.data['mt_count'] = mt_len
        return sale_price_sum, mt_len
    #获取好评数
    def get_good_num(self) -> int:

        url_comment = "https://e.dianping.com/review/app/index/ajax/pcreview/listV2"
        query    = {
            "platform": "1",
            "shopIdStr": "1340799757",
            "tagId": "1",
            "startDate": self.date.strftime('%Y-%m-%d'),
            "endDate": self.date.strftime('%Y-%m-%d'),
            "pageNo": "1",
            "pageSize": "20",
            "referType": "0",
            "category": "0",
            "yodaReady": "h5",
            "csecplatform": "4",
            "csecversion": "3.1.0",
            "mtgsig": {"a1":"1.2","a2":1759267349750,"a3":"1758131109387IKYIQGEfd79fef3d01d5e9aadc18ccd4d0c95072322","a5":"ZBfDwtpBGm/4861YBNXYOb9mq2jM67slNpkwsyYQvMEv4i0pRkAdYL/aq+yY3D3YoxWPL9Jr9a6CLB3E92ADGkRpDI==","a6":"hs1.6L0z6EnhuTEwFP0z8lbe5KAB4hoOQPGpFzKfoc++lOA8A5EuPyOWvi2SUzNZqSofxso8gn3E49lCDQV73NVvrg6KsbCuuwQDbtHc7L4oF6ozsxnxgTo7dPlc9LxYaYK1i","a8":"29597c60f176e49f8ccca3345445f252","a9":"4.0.4,7,94","a10":"67","x0":4,"d1":"f66d474c144fa9e1a5af8b0fe222eea0"}
        }

        headers_comment = {
            **common_headers,
            "Host": "e.dianping.com",
            "Pragma": "no-cache",
            "Referer": "https://e.dianping.com/vg-platform-reviewmanage/shop-comment-mt/index.html"
            
        }
        response = requests.get(url=url_comment, params = query, cookies = cookies ,headers = headers_comment)
        data_json = response.json()
        high_rates = data_json.get('data', {}).get('highRateReviewNum', 0)
        self.data['mt_good'] = high_rates
        return high_rates

def get_meituanSum(date: datetime) -> Tuple[float, int]:
    """
    获取指定日期的美团订单总金额和订单数量。
    返回: (总金额, 订单数量)
    """
    # 设定起止时间（当日 00:00:00 - 23:59:59）
    today_start = datetime(date.year, date.month, date.day)
    today_end = today_start + timedelta(hours=23, minutes=59, seconds=59)

    logger.info(f'美团数据日期 {today_start.strftime("%Y-%m-%d")}')

    # 转换为毫秒级 Unix 时间戳
    begin_timestamp = int(today_start.timestamp() * 1000)
    end_timestamp = int(today_end.timestamp() * 1000)

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

    json_data: Optional[Dict[str, Any]] = None
    sale_price_sum = 0.0
    mt_len = 0

    try:
        response = requests.post(url=mt_api, headers=headers, json=data, cookies=cookies)
        #breakpoint()
        response.raise_for_status()
        json_data = response.json()

        if not json_data:
            logger.error('美团请求返回空值，请检查 cookie 是否失效')
            chosen = input("还要继续执行吗? N/y ").strip() or "N"
            #compitable with python 3.10+
            # match chosen.lower():
            #     case "y":
            #         print("继续执行...")
            #         # 执行逻辑
            #     case _:
            #         print("程序终止，请检查Cookies")
            #         sys.exit(2)
            if chosen.lower() == 'y':
                print("继续执行...")
            else:
                print("程序终止，请检查Cookies")
                sys.exit(2)


        # 保存 JSON 响应
        os.makedirs(f"{proj_dir}/meituan", exist_ok=True)
        with open(f"{proj_dir}/meituan/meituan.json", 'w', encoding="utf-8") as data_json:
            json.dump(json_data, data_json, ensure_ascii=False, indent=4)

#    except RequestException as e:
#        logger.error(f"请求失败: {e}")
    except json.JSONDecodeError:
        logger.error("响应不是合法 JSON")
        
        logger.error(locals().get("response", "没有美团的返回数据"))
        chosen = input("还要继续执行吗? N/y ").strip() or "N"

        # match chosen.lower():
        #     case "y":
        #         print("继续执行...")
        #         # 执行逻辑
        #     case _:
        #         print("程序终止，请检查Cookies")
        #         sys.exit(2)
        if chosen.lower() == 'y':
            print("继续执行...")
        else:
            print("程序终止，请检查Cookies")
            sys.exit(2)

    # 处理返回数据
    if json_data:
        data = json_data.get("data", {})
        couponRecordDetails = data.get("couponRecordDetails", [])
        mt_len = data.get("recordSum", 0)

        i=0
        ouput_price: str = " \n"
        if couponRecordDetails:
            logger.info('美团列表')
            for i, record in enumerate(couponRecordDetails, start=1):
                price_str = record.get("salePrice", "")
                #logger.info(f'{price_str}\t')
                ouput_price += f" {price_str}\n"

                try:
                    sale_price = float(price_str.replace("¥", "").strip())
                except ValueError:
                    logger.warning(f"无法解析价格: {price_str}")
                    continue

                sale_price_sum += sale_price
            logger.info(ouput_price)

            sale_price_sum = round(sale_price_sum, 2)
            logger.info(f'总计 {i} 单')

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
    high_rates = data_json.get('data', {}).get('highRateReviewNum', 0)
 
    return high_rates
    

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

