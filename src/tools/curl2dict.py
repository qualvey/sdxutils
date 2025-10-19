import re
import requests
import json

def curl_to_requests(curl_command):
    """
    将原始 cURL 字符串转换为 requests 库可用的格式。

    Args:
        curl_command (str): 原始 cURL 字符串。

    Returns:
        tuple: 包含 requests 方法、URL、headers、数据（如果存在）的元组。
    """

    # 解析 URL
    url_match = re.search(r"'(https?://[^']+)'", curl_command)
    if not url_match:
        raise ValueError("无法解析 URL。")
    url = url_match.group(1)

    # 解析 HTTP 方法
    method = "GET"  # 默认 GET
    if "-X" in curl_command:
        method_match = re.search(r"-X\s+'(\w+)'", curl_command)
        if method_match:
            method = method_match.group(1).upper()
    elif "-d" in curl_command or "--data" in curl_command:
        method = "POST"  # 如果有数据，则默认为 POST

    # 解析 headers
    headers = {}
    header_matches = re.findall(r"-H\s+'([^:]+):\s*([^']+)'", curl_command)
    for key, value in header_matches:
        headers[key] = value

    # 解析 data
    data = None
    if "-d" in curl_command or "--data" in curl_command:
        data_match = re.search(r"(?:-d|--data)\s+'({.+?})'", curl_command) # 尝试json
        if data_match:
            try:
                data = json.loads(data_match.group(1))
            except json.JSONDecodeError:
                data_match = re.search(r"(?:-d|--data)\s+'(.+?)'", curl_command) # 尝试普通data
                if data_match:
                    data = data_match.group(1)
        else:
            data_match = re.search(r"(?:-d|--data)\s+'(.+?)'", curl_command) # 尝试普通data
            if data_match:
                data = data_match.group(1)

    return method, url, headers, data

# 示例用法
curl_command = """
curl 'http://nas.nebulaol.com:88/webapi/entry.cgi/SYNO.SynologyDrive.Files/2025%E5%B9%B4%E6%97%A5%E6%8A%A5%E8%A1%A8.xlsx?api=SYNO.SynologyDrive.Files&method=download&version=2&download_type=%22download%22&files=%5B%22id%3A871388255306693754%22%5D&force_download=true&json_error=true&_dc=1741723830147&SynoToken=YcOwtSgHT1sGI' \
-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0' \
-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
-H 'Accept-Language: zh,en-US;q=0.7,en;q=0.3' 
-H 'Accept-Encoding: gzip, deflate' \
-H 'Connection: keep-alive' \
-H 'Referer: http://nas.nebulaol.com:88/?launchApp=SYNO.SDS.Drive.Application' \
-H 'Cookie: _SSID=UUbSpaMlyL0ZIuLt_PQ5EvZ4GPbGqS6Zc5h7GqutzTE; stay_login=1; did=MyQrIAF_MTALvdhP9xKhpyWLRyqZrLQzkA492Xhen3tby8jSZDQ93pWSi-plzx4ZuHIGNp5zhgHEOePzaB-p2Q; _CrPoSt=cHJvdG9jb2w9aHR0cDo7IHBvcnQ9ODg7IHBhdGhuYW1lPS87; id=P9wF9_9yQcMrqqu2UbLFaAerG0RyBcMJkgsWZwWotzotgnTR3LDaNezAB0IaNtSOBSWcHlH4Sr8tt6nKhR7ZJQ; io=ph5CXxV0ezAGPUTTADRM; {e0c3b0cc-2222-413f-98b2-2d8043736576}=value' \
-H 'Upgrade-Insecure-Requests: 1' \
-H 'Priority: u=4'
"""

method, url, headers, data = curl_to_requests(curl_command)

print("Method:", method)
print("URL:", url)
print("Headers:", headers)
print("Data:", data)

# 使用 requests 库构建请求
if method == "GET":
    response = requests.get(url, headers=headers)
elif method == "POST":
    if isinstance(data, dict):
        response = requests.post(url, headers=headers, json=data)
    else:
        response = requests.post(url, headers=headers, data=data)

print(response.text)
