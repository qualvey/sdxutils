import requests
import json
from urllib.parse import urlparse, parse_qs

raw_request = """
POST /life/trade_view/v1/verify/verify_record_list/?page_index=1&page_size=20&industry=industry_common&root_life_account_id=7136075595087087628 HTTP/2
Host: life.douyin.com
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
Accept: application/json, text/plain, */*
Accept-Language: zh,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate, br, zstd
Content-Type: application/json
Content-Length: 288
Referer: https://life.douyin.com/p/liteapp/fulfillment-fusion/record?enter_from=home_verify_history&groupid=1742205968991236&view_type=view_verify_record
Agw-Js-Conv: str
x-tt-ls-session-id: dbb14a64-0971-4299-9a19-7f6ce1e29167
x-tt-trace-log: 01
x-tt-trace-id: 00-82a553d5187d8c27298d491cb-82a553d5187d8c27-01
Ac-Tag: smb_s
rpc-persist-life-merchant-role: 0
rpc-persist-life-merchant-switch-role: 1
rpc-persist-life-biz-view-id: 0
rpc-persist-lite-app-id: 100281
rpc-persist-life-platform: pc
rpc-persist-terminal-type: 1
rpc-persist-session-id: 1002813e-ce28-4606-a1d0-fd848c6e794b
x-secsdk-csrf-token: 0001000000013b5f45ec5a2257c4e0bb4dcb9871ee0c2130458b7e05e2e62aa9ab896ab8072d182b8a13a8c60168
Origin: https://life.douyin.com
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Connection: keep-alive
Cookie: ttwid=1%7CCH6FwiOjTAmdMtNErdplHinGqqdXycoGnFE4Kd4jGzc%7C1741637497%7C92f13873e5863237370f82fbf39286ec1b8586302eb62e2c726f2db332d5db7e; passport_csrf_token=c5cac90e5f2483a05e2e50efe624dc6e; passport_csrf_token_default=c5cac90e5f2483a05e2e50efe624dc6e; odin_tt=76a6f66549a72a8314b3a95536f71c44152ec87eaf14a6870f8b31e91ad4010b851171a2e5848cab358f9111cac99569; passport_auth_status_ls=824a9c7f166375a6cc8e7154726d5278%2C; passport_au
Priority: u=0
TE: trailers
"""

# 分割请求头和请求体
headers_str, data_str = raw_request.split('\n\n', 1)

# 解析请求行
request_lines = headers_str.split('\n')
request_line = request_lines[0].split(' ')
method = request_line[0]
url = "https://life.douyin.com" + request_line[1]
parsed_url = urlparse(url)
query_params = parse_qs(parsed_url.query)

# 解析请求头
headers = {}
cookies = {}
for line in request_lines[1:]:
    if line:
        key, value = line.split(': ', 1)
        if key == "Cookie":
            cookie_pairs = value.split("; ")
            for pair in cookie_pairs:
                cookie_key, cookie_value = pair.split("=", 1)
                cookies[cookie_key] = cookie_value
        else:
            headers[key] = value

# 解析请求体
data = json.loads(data_str) if data_str else None

# 构建 Python 字典
request_data = {
    "url": url,
    "headers": headers,
    "cookies": cookies,
    "json": data,
}

# 打印JSON
print(json.dumps(request_data, indent=4))
