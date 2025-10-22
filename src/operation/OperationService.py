import requests,json

from tools import env
from tools import HeaderService
from datetime import  datetime
from tools import LoggerService
logger = LoggerService(__name__).logger

header_service = HeaderService()
headers = header_service.headers
#TODO: add token to headers, add parameter with token

class OperationService:
    def __init__(self,datetime:datetime,token:str):
        self.headers = headers
        self.headers['Authorization'] = token
        self.scheme = 'https://'
        self.hostname = headers['Host']
        self.base_url = f"{self.scheme}{self.hostname}"
        self.headers = headers
        self.datetime = datetime
        self.data = {}
        self.run()

    def fetch_data(self) -> dict:
        date_str =self.datetime.strftime('%Y-%m-%d')
        logger.info(f'date:{date_str}')
        params = {
            'branchId': 'a92fd8a33b7811ea87766c92bf5c82be',
            'startTm' : f'{date_str} 00:00:00'
        }
        api_path_prefix = '/api/statistics/branch/operation/data'
        api_map         = {
            'income':   f'{api_path_prefix}/income/info',
            'data'  :   f'{api_path_prefix}/info',
            'state' :   f'{api_path_prefix}/state'
        }

        all_data = {}

        for api_name, api_endpoint in api_map.items():

            url = f"https://{headers['Host']}{api_endpoint}"
            response = requests.get(url, params = params, headers=headers, timeout=10)
            response_data = response.json()
            # fmt_response  = json.dumps(response_data, indent=4)
            #breakpoint()
            if response.status_code == 200 and 'data' in response_data:
                try:
                    all_data[api_name] = response_data['data']  # 将 JSON 响应保存到字典中
                except json.JSONDecodeError:
                    logger.warning(f"警告: {api_name} API 响应不是有效的 JSON。")
                    all_data[api_name] = response.text  # 如果不是 JSON，保存原始文本
            else:
                logger.error("content",response.content)
                logger.error(f"请求 {api_name} API 失败：{response.status_code} token错误")
                all_data[api_name] = {"error": f"请求失败：{response.status_code}"}  # 记录错误信息
        return all_data
    
    def merge_data(self,all_data) -> dict:
        merged_data = {}
        target_file = f"{env.proj_dir}/src/operation/operaton.json"
        if all(isinstance(data, dict) for data in all_data.values()): # 检查是否都是json
            for data in all_data.values():
                for key, value in data.items():
                    if value != 0:
                        merged_data[key] = value

            with open(target_file, "w", encoding="UTF-8") as target:
                    json.dump(merged_data, target, ensure_ascii=False, indent=4)
                    logger.info(f"合并后的 API 数据已写入 {target_file} 文件中。")
        else:
            logger.error("API 响应不是全部为 JSON，无法合并。")
        return merged_data

    def resolve_operation_data(self, data:dict) -> dict:
        path = f"{env.proj_dir}/src/operation/unmerged_data.json"
        with open(path, 'w') as f :
            json.dump(data, f, ensure_ascii=False, indent=4)
        merged_data = self.merge_data(data)

        return merged_data
    
    def run(self):
        self.data = self.resolve_operation_data(self.fetch_data())
    def resolve_data(self,data:dict) -> int:
        income = data['turnoverSumFee']
        return(income)

    def today_income(self,date:datetime) -> int:
        op_data = self.resolve_operation_data(self.fetch_data())
        out  = self.resolve_data(op_data)
        return out

if __name__ == '__main__':
    #depcrecated below
    # op = OperationService(datetime.today())
    # #print(today_income(datetime.today()))
    # date_str = datetime.strptime('2025-04-01', '%Y-%m-%d')
    # #data = resolve_operation_data(datetime.today())
    # data = op.resolve_operation_data(op.fetch_data())
    # form_data = json.dumps(data, indent=4)
    # print(form_data.__class__)
    pass