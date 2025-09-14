import requests
import json
from tools import env
from tools.iheader import headers
from datetime import  datetime
from tools import logger as mylogger

logger = mylogger.get_logger(__name__)

def merge_data(all_data):
    merged_data = {}
    target_file = f"{env.proj_dir}/operation/operaton.json"
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


def resolve_operation_data(datetime_obj):

    date_str = datetime_obj.strftime('%Y-%m-%d')
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
        fmt_response  = json.dumps(response_data, indent=4)
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

    path = f"{env.proj_dir}/operation/unmerged_data.json"
    with open(path, 'w') as f :
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    merged_data = merge_data(all_data)

    return merged_data

def resolve_data(data):

    income = data['turnoverSumFee']
    return(income)

def today_income(datetime_obj):
    op_data = resolve_operation_data(datetime_obj)
    out  = resolve_data(op_data)
    return out

if __name__ == '__main__':

    #print(today_income(datetime.today()))
    date_str = datetime.strptime('2025-04-01', '%Y-%m-%d')
    #data = resolve_operation_data(datetime.today())
    data = resolve_operation_data(date_str)
    form_data = json.dumps(data, indent=4)
    print(form_data.__class__)
