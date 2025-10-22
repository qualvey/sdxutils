from tools import HeaderService,LoggerService
import requests,math, json

from collections import defaultdict
from datetime import datetime

logger = LoggerService(__name__).logger

header_service = HeaderService()
headers = header_service.headers
# # 公共请求头
# raw_header = """ Host: hub.sdxnetcafe.com
# User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
# Accept: application/json, text/plain, */*
# Accept-Language: zh,en-US;q=0.7,en;q=0.3
# Accept-Encoding: gzip, deflate, br, zstd
# Content-Type: application/json;charset=utf-8
# Origin: https://hub.sdxnetcafe.com
# Connection: keep-alive
# Referer: https://hub.sdxnetcafe.com/
# Sec-Fetch-Dest: empty
# Sec-Fetch-Mode: cors
# Sec-Fetch-Site: same-origin
# Priority: u=0
# """

# headers = {"Authorization": Iheaders['Authorization']}
# for line in raw_header.splitlines():
#     if line.strip():
#         key, value = line.split(":", 1)
#         headers[key.strip()] = value.strip()

SAVE_URL = 'https://hub.sdxnetcafe.com/api/admin/third/income/save'


class ThirdPartyError(Exception):
    """第三方数据请求失败"""
    pass


class ThirdPartyResponseError(Exception):
    """第三方数据返回异常"""
    pass

#todo: add token to headers, add parameter with token, OOP design

class OTAUpdater:
    """OTA 数据更新工具"""

    def __init__(self, data: dict, date: datetime, token: str):
        self.hostname = 'hub.sdxnetcafe.com'
        self.date = date
        self.data = data
        headers['Authorization'] = token
        logger.debug(f'初始化 OTAUpdater，日期: {self.date}, 数据: {json.dumps(self.data, ensure_ascii=False)}')
        self.duplicated_ids = defaultdict(list)

    def _get_list(self, page: int, limit: int, startTm: str, endTm: str) -> dict:
        """请求 API，获取指定时间范围的数据列表"""
        api = (
            f'https://{self.hostname}/api/admin/third/income/pageList'
            f'?branchId=a92fd8a33b7811ea87766c92bf5c82be'
            f'&startTm={startTm}&endTm={endTm}&page={page}&limit={limit}'
        )
        response = requests.get(url=api, headers=headers, timeout=10, verify=True)
        if response.status_code != 200:
            raise ThirdPartyError(f"请求失败: {response.status_code}")
        return response.json()

    def _collect_duplicates(self, date_str: str, item_list: list):
        """检查重复数据并记录 ID"""
        for item in item_list:
            if item['reportDate'] == date_str:
                third_type = item['thirdType']
                item_id = item['id']
                self.duplicated_ids[third_type].append(item_id)
                logger.warning(f'已经存在 {third_type}，需要删除重新更新')

    def check_unique(self) -> dict:
        """检查某日期是否已有数据，返回重复数据 ID"""
        date_str = self.date.strftime("%Y-%m-%d")
        limit = 30
        startTm = f'{date_str} 00:00:00'
        endTm = f'{date_str} 23:59:59'

        response_list = self._get_list(page=1, limit=limit, startTm=startTm, endTm=endTm)
        total = response_list['data']['total']
        data_list = response_list['data']['rows']
        self._collect_duplicates(date_str, data_list)

        if total > limit:
            pages = math.ceil(total / limit)
            for page in range(2, pages + 1):
                response_list = self._get_list(page=page, limit=limit, startTm=startTm, endTm=endTm)
                data_list = response_list['data']['rows']
                self._collect_duplicates(date_str, data_list)

        logger.debug(f'重复数据: {json.dumps(self.duplicated_ids, ensure_ascii=False, indent=4)}')
        return self.duplicated_ids

    def delete(self, record_id: str) -> bool:
        """删除指定记录"""
        api = f'https://{self.hostname}/api/admin/third/income/delete/{record_id}'
        response = requests.get(url=api, headers=headers, timeout=7)
        res_json = response.json()
        if res_json.get('status') == 200:
            logger.info(f'删除成功, id={record_id}')
            return True
        else:
            logger.error(f'删除失败, id={record_id}, 返回: {res_json}')
            return False

    def update(self, name: str, income: int) -> dict:
        """更新某渠道的数据"""
        date_str = self.date.strftime("%Y-%m-%d")
        data = {
            "branchId": "a92fd8a33b7811ea87766c92bf5c82be",
            "reportDate": date_str,
            "thirdType": name,
            "income": income
        }
        logger.info(f'正在更新 {name} 的数据: {data}')
        response = requests.post(url=SAVE_URL, headers=headers, json=data, timeout=10, verify=True)
        logger.info(f'更新 {name} 返回结果: {response.text}')
        return response.json()

    def run(self):
        """整体执行逻辑：删除重复 → 更新数据"""
        duplicates = self.check_unique()
        for third_type, ids in duplicates.items():
            for rid in ids:
                self.delete(rid)

        for name in ["meituan", "douyin"]:
        
            income = self.data.get(name, {}).get(f"{name}_total", 0)
            self.update(name, income)
