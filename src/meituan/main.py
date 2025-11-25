
import argparse, os, sys, json, requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from tools import env

from typing import Any, Dict, Tuple, Optional

from tools import LoggerService
logger = LoggerService(__name__).logger


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
        self.discount_price_sum = 0.0
        self.data = {}
        self.get_meituan_sum()
        # self.get_discount_sum()
        self.get_good_num()

    def get_discount_sum(self) -> None:
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

        response = requests.post(url=mt_api, headers=headers, json=request_data, cookies=cookies)
        response.raise_for_status()
        json_data = response.json()
        if not json_data:
            raise ValueError("美团请求返回空值，请检查 cookie 是否失效")

        data = json_data.get("data", {})
        coupon_records = data.get("couponRecordDetails", [])

        import re
        for record in coupon_records:
            price_str = record.get("salePrice", "")
            discount_str = record.get("discountPrice", "")
            try:
                match = re.search(r"([\d.]+)", discount_str)
                discount_price = float(match.group(1)) if match else None
                self.discount_price_sum += discount_price if discount_price is not None else 0.0
     
            except ValueError:
                logger.warning(f"无法解析价格: {price_str}")
        print(f'today discount:{self.discount_price_sum}')
        
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
        if not response.content:
            logger.warning("美团请求返回空值，请检查 cookie 是否失效")
            raise ValueError("美团请求返回空值，请检查 cookie 是否失效")
            
        response.raise_for_status()
        json_data = response.json()
        if not json_data:
            raise ValueError("美团请求返回空值，请检查 cookie 是否失效")

        # 保存 JSON 响应
        os.makedirs(f"{proj_dir}/meituan", exist_ok=True)
        with open(f"{proj_dir}/src/meituan/meituan.json", 'w', encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        if json_data.get("code") == 200:
            logger.info("美团数据获取成功")
        else:
            logger.warning(f"美团数据获取异常，返回码: {json_data.get('code')}")

        data = json_data.get("data", {})
        coupon_records = data.get("couponRecordDetails", [])
        if coupon_records is None:
            logger.info("美团无订单数据")
            return 0.0, 0
        mt_len = data.get("recordSum", 0)
        import re
        for record in coupon_records:
            price_str = record.get("salePrice", "")
            discount_str = record.get("discountPrice", "")
            try:
                match = re.search(r"([\d.]+)", discount_str)
                discount_price = float(match.group(1)) if match else None
                self.discount_price_sum += discount_price if discount_price is not None else 0.0
                sale_price = float(price_str.replace("¥", "").strip())
                sale_price_sum += sale_price
            except ValueError:
                logger.warning(f"无法解析价格: {price_str}")
        sale_price_sum = round(sale_price_sum, 2)
        #实际收入 = 销售总额 - 折扣总额,取消了
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
        with open(f"{proj_dir}/src/meituan/meituan_comments.json", 'w', encoding="utf-8") as f:
            # json.dump(data_json, f, ensure_ascii=False, indent=4)
            pass
            #这里的json字段可能会变动，需要注意
            #msg->reviewDetailDTOs-star==5
        high_rates = 0
        for i in data_json.get('msg', {}).get('reviewDetailDTOs', []):
            if i.get('star', 0) == 50:
                high_rates += 1

        self.data['mt_good'] = high_rates
        return high_rates
