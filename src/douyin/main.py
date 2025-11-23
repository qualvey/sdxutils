
import json, time,requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from tools import env
from tools import LoggerService
logger = LoggerService(__name__).logger

from typing  import Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

#just paste the link here to extract parameters
origin_url:str = "https://life.douyin.com/life/infra/v1/review/get_review_list/?life_account_ids=7548743672642127912&poi_id=6828149180763080708&tags=1,9,5,4,10,8,7,50,&sort_by=2&life_account_id=7136075595087087628&query_time_start=1759161600&query_time_end=1759247999&search_after=&cursor=0&count=10&top_rate_ids=&reply_display_by_level=1&root_life_account_id=7136075595087087628&store_type=2&source=1"
cookie:str         = env.configjson['cookies']['dy']
# Convert cookie string to dict if necessary
def parse_cookie_string(cookie_str: str) -> dict:
    return dict(item.strip().split("=", 1) for item in cookie_str.split(";") if "=" in item)

cookies_dict = parse_cookie_string(cookie) if isinstance(cookie, str) else cookie

output_path:str = f"{env.proj_dir}/src/douyin/douyin.json"

common_headers:dict = {
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
specific_headers:dict = {
        "x-tt-trace-id": "00-833c459518ddb35cb728491cb-833c459518ddb35c-01",
        "rpc-persist-session-id": "100281b8-90cf-4fe7-acdc-4568a43d7667",
        "x-secsdk-csrf-token": "000100000001ca5a6af103350fc8059c84b0e50942e3f3a8686a721e2fdce8ba3cb75158d32118377800f3fe4702",
        "x-tt-ls-session-id": "670c204f-500f-41dc-8123-51da77a17d0e",
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    }
#python 3.9+
headers = common_headers | specific_headers
#for Python < 3.9
# headers = {**common_headers, **specific_headers}
def extract_params(url: str) -> dict:
    # 解析 URL
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    # 需要的 key
    keys = ["root_life_account_id", "life_account_ids", "life_account_id", "poi_id"]

    # 提取并返回
    result = {}
    for key in keys:
        if key in query:
            # parse_qs 返回的是 list，所以取第一个
            result[key] = query[key][0]
        else:
            result[key] = None
    return result

key_params = extract_params(origin_url)

class DouyinRequestError(Exception):
    """抖音数据请求失败（重试已达最大次数）"""
    pass

class DouyinService:
    #needed parameters
    # https://life.douyin.com/life/infra/v1/review/get_review_list/?life_account_ids=7548743672642127912&poi_id=6828149180763080708&tags=1,9,5,4,10,8,7,50,&sort_by=2&life_account_id=7136075595087087628&query_time_start=1759161600&query_time_end=1759247999&search_after=&cursor=0&count=10&top_rate_ids=&reply_display_by_level=1&root_life_account_id=7136075595087087628&store_type=2&source=1

        # root_life_account_id
        # life_account_ids
        # life_account_id
        # root_life_account_id
        # poi_id
    # 
    def __init__(self,date:datetime) -> None:
        self.date = date
        self.dy_rawdata = {}
        self.data = {}  # Always initialize as dict
        self.fetch_douyin_data()
        self.resolve_douyin_data()
        self.get_dygood_rate()
      

    def fetch_douyin_data(self,
        session: Optional[requests.Session] = None,
        headers: Optional[dict] = headers,
        cookies: Optional[dict] = cookies_dict,
        output_path: Optional[str] = output_path,
        max_retries: int = 5,
        delay: int = 2
    ) -> Optional[dict]:
        
        url = "https://life.douyin.com/life/trade_view/v1/verify/verify_record_list/"

        params  = {
            'page_index': 1,
            'page_size' : 100, 
            'root_life_account_id' : key_params['root_life_account_id'],
            
        }
        logger.info(f'抖音日期:{self.date}')

        time_start = datetime(self.date.year, self.date.month, self.date.day)
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
                session = session or requests.Session()
                response = session.post(url, params=params, json=post_data, headers=headers, cookies=cookies)
                response.raise_for_status()  # 如果状态码不是 200，抛出异常
                douyin_json = response.json()

                if douyin_json:
                    logger.info("获取抖音数据成功.")
                    logger.debug(f'详细原始json:{json.dumps(douyin_json, indent=4, ensure_ascii=False)}')

                    status_code = douyin_json.get("status_code")
                    if status_code == 4000100:
                        raise ValueError("鉴权失败，cookie 可能过期")
                with open(f"{output_path}", 'w', encoding='utf-8') as data_json:
                    json.dump(douyin_json, data_json, ensure_ascii=False, indent=4)
                self.dy_rawdata = douyin_json
                return douyin_json  # 请求成功，返回 JSON 数据
            
            except requests.exceptions.RequestException as e:
                logger.error(f"请求发生错误（第 {attempt+1} 次尝试）：{e}")

                if attempt < max_retries - 1:  # 如果还有重试机会，等待后重试
                    time.sleep(delay)  # 等待 delay 秒后重试
                else:
                    raise DouyinRequestError("抖音已达到最大重试次数，放弃请求")

    def resolve_douyin_data(self) -> Tuple[Decimal, int]:
        total: Decimal = Decimal("0.0")
        output: str = "\n"
        dy_json = self.dy_rawdata

        if not dy_json:
            raise ValueError("没有可解析的抖音数据")
        try:
            dy_data = dy_json.get('data')
            if dy_data is None:
                raise ValueError('返回中缺少 "data" 字段')
            
            dy_list = dy_data.get('list')
            if dy_list:
                dy_len = len(dy_list)
                logger.info("抖音列表")
                for item in dy_list:
                    raw_amount = item['amount']['verify_amount']  # 单位是分？
                    amount = Decimal(raw_amount) / Decimal("100")  # 单位转元
                    #logger.info(f"{amount}")
                    output += f"{amount}\n"
                    total += amount

                logger.info(output)
            else:
                dy_len = 0
        except KeyError as e:
            raise ValueError(f"解析数据失败：缺失关键字段 {e}") from e
        dy_total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if not isinstance(self.data, dict):
            self.data = {}
        self.data['douyin_total'] = float(dy_total)
        self.data['dy_count'] = dy_len
        return dy_total , dy_len

    def get_dygood_rate(self) -> int:
        date = self.date
        date_start = datetime(date.year, date.month, date.day)
        date_end = date_start + timedelta(hours=23, minutes=59, seconds=59)

        # 转换为 Unix 时间戳（单位：秒）
        # datetime对象有timestamp方法
        begin_timestamp = int(date_start.timestamp())
        end_timestamp   = int(date_end.timestamp())

        url      = "https://life.douyin.com/life/infra/v1/review/get_review_list/"
        
        #几个id可能会改变 
        query  = {
            # "life_account_ids": "7548743672642127912",
            # "life_account_id": "7136075595087087628",
            # "root_life_account_id": "7136075595087087628",
            # "poi_id": "6828149180763080708",
            **key_params,
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
            cookies = cookies_dict
            )

        data = response.json()
        review_path = f"{env.proj_dir}/src/douyin/douyin-review.json"
        with open(review_path, 'w', encoding='utf-8') as review_json:
            json.dump(data, review_json, ensure_ascii=False, indent=4)
        logger.debug(f"get_good_rate返回json:\n{json.dumps(data, indent = 4, ensure_ascii=False)}")
        response_list = data.get('data').get('reviews')
        logger.debug('get_good_rate:\n')
        logger.debug(json.dumps(response_list, indent = 4, ensure_ascii=False))
        if response_list is not None:
            list_len = len(response_list)
            if not isinstance(self.data, dict):
                self.data = {}
            self.data['dy_good'] = list_len

            return list_len
        else:
            self.data['dy_good'] = 0
            return 0

    def final_out(self) ->  Optional[Tuple[Decimal, int]]:
        try:
            data = self.fetch_douyin_data( headers=headers, cookies=cookies_dict, output_path=output_path )
            if not data:
                raise ValueError('请求返回失败')
            result = self.resolve_douyin_data()
            good_rate = self.get_dygood_rate()
            logger.info(f"好评数：{good_rate}")
            return result
        except Exception as e:
            logger.warning(f"final_out 失败：{e}")
            return None


