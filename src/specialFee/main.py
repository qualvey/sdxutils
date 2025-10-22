import requests,    json

from datetime import datetime

from tools    import env, HeaderService
from typing import Optional

from tools import LoggerService
logger = LoggerService(__name__).logger

scheme = 'https://'
headers = HeaderService().headers
hostname = headers['Host']
# {'detail':resolved_data, 'sum':total_fee}

class SpecialFee:
    def __init__(self,date:datetime, token:str):
        self.date = date
        headers['Authorization'] = token
        self.data = {}
        self.run()
        
    def fetch_specialFee(self) -> dict:
        date_str = self.date.strftime('%Y-%m-%d')
        api_path = '/api/payment/order/specialFree/list'
        params   = {
            'orderNo': '',
            'page'  : 1,
            'limit' : 100,
            'sortName': 'submitAt',
            'sortOrder': 'desc',
            'branchId' : 'a92fd8a33b7811ea87766c92bf5c82be',
            'startTm'  : f'{date_str} 00:00:00',
            'endTm'    : f'{date_str} 23:59:59'
        }
        url = f"{scheme}{hostname}{api_path}"
        response = requests.get(url,params = params,  headers=headers)
        data     = response.json()
        with open(f"{env.proj_dir}/src/specialFee/special.json", "w", encoding="UTF-8") as cache:
            json.dump(data, cache, ensure_ascii=False, indent=4)
        return data

    def resolve_data(self,data:dict) -> dict:
        special_reason_totals = {}
        
        for item in data.get('data',{}).get('rows',[]):
            if item['status']=='COMPLETED':
            #status有可能是其他状态，比如 "CANCELLED"
                reason = item['specialReason']
                amount = float(item['totalAmount'])  # 将金额转换为浮点数
                amount_int = int(amount)

                if "吃鸡" in reason or '游戏' in reason:
                    reason = "游戏奖励"
                # 如果 specialReason 已在字典中，累加金额；否则，初始化为当前金额
                if reason in special_reason_totals:
                    special_reason_totals[reason] += amount_int
                else:
                    special_reason_totals[reason] = amount_int
        #breakpoint()
        return special_reason_totals

    def get_special_list(self,data, special_code, reverse=False) -> Optional[list]:

        #用dict数据结构来存储
        speciallist = []
        if special_code:
            return None
        else:
            # 根据 reverse 参数决定排序顺序
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=reverse)
            # 计算 reason 字段的最大长度
            max_reason_length = max(len(reason) for reason, _ in sorted_items)

            for index, (reason, total) in enumerate(sorted_items, start=1):
                # logger.info(reason)
                raw_padding = (max_reason_length - len(reason)) * 3
                padding_length = max(min(raw_padding, 3), 6)
                width  = max_reason_length + padding_length
                assert width >= 0, f"格式化宽度不能为负数，但现在是 {width}"
                item = f"{index}. {reason:<{width}}:{total}"
                speciallist.append(item)
            return speciallist

    def get_specialFee(self,special_reason_totals:dict) -> int:

        sum  = 0 
        for (name, value) in special_reason_totals.items():
            sum += value

        # speciallist = format_specialFee(special_reason_totals,special_code)

        return  sum

    def run(self):
        sf_data = self.fetch_specialFee()
        resolved_data = self.resolve_data(sf_data)
        total_fee = self.get_specialFee(resolved_data)
        self.data = {'detail':resolved_data, 'sum':total_fee}