
import requests
import json
from tools import env
#from tools.iheader import headers
import datetime

time = datetime.time
datetime = datetime.datetime

def get_headers():
    raw_header = """
    Host: hub.sdxnetcafe.com
    User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
    Accept: application/json, text/plain, */*
    Accept-Language: zh,en-US;q=0.7,en;q=0.3
    Accept-Encoding: gzip, deflate, br, zstd
    Connection: keep-alive
    Referer: https://hub.sdxnetcafe.com/
    Sec-Fetch-Dest: empty
    Sec-Fetch-Mode: cors
    Sec-Fetch-Site: same-origin
    Priority: u=0
    """
    headers = {}
    token = 'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJsaWxvbmd0YW8iLCJ1c2VySWQiOiJmNjhmMGIzM2M4ZTAxMWVmYTJkOGI4NTk5ZmM5MDk2YyIsIm5hbWUiOiLmnY7pvpnmtpsiLCJleHAiOjE3NDQ0MTIzNzB9.M3hpUlSs184WPHKYd5AlTgoxdTYEPbJSgdi-XHeXaoUXX4UokKL8l0x7jXZoZBAFyHgMmqMySpOMw9JzJENkW0P-omtyuGlkwU-k8JP6GF_uDbxpLu5mvIfFppT3yKYzgxKRF-izAvAdieIsEDwbHlIk0JtVHX2y4cG85fa3Rd8'
    headers['Authorization'] = token

    def raw_header_to_json(raw_header):
        lines = raw_header.splitlines()
        for line in lines:
            if line.strip():
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        return headers
    headers = raw_header_to_json(raw_header)
    return headers

def fetch_operation_data():
    headers = get_headers()
    date = '2025-04-10'
    branchId = "a92fd8a33b7811ea87766c92bf5c82be"
    state =     f"/api/statistics/branch/operation/data/state?branchId={branchId}&startTm={date}+00:00:00"
    
    #url = f"https://{headers['Host']}{API_ENDPOINTS['state']}"
    url = f"https://{headers['Host']}{state}"
    response = requests.get(url, headers=headers, timeout=10)
    response_data = response.json()
    if response.status_code == 200 and 'data' in response_data:
        data = response_data['data']  # 将 JSON 响应保存到字典中
    income = data['turnoverSumFee']
    return(income)



if __name__ == '__main__':
    data =   fetch_operation_data()
    print(data)

def operation():

    branchId = "a92fd8a33b7811ea87766c92bf5c82be"
    date = request.args.get('date')
    api_endpoint =  f"/api/statistics/branch/operation/data/income/info?branchId={branchId}&startTm={date}+00:00:00",
    url = f"https://{headers['Host']}{api_endpoint}"

    logger.debug(f'operation headers:{headers}\n token: {token} \ndate: {date}\nurl: {url}')

    response = requests.get(url, headers=headers, timeout=10)
    response_data = response.json()
    if response.status_code == 200 and 'data' in response_data:
        try:
            all_data = response_data['data']  # 将 JSON 响应保存到字典中
        except json.JSONDecodeError:
            print(f"警告: {api_name} API 响应不是有效的 JSON。")
            all_data[api_name] = response.text  # 如果不是 JSON，保存原始文本

    income =all_data['turnoverSumFee']
    return  jsonify({'income': income})
