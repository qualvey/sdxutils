from tools import login

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
token = login.init()
headers = {}
headers['Authorization'] =token 

def raw_header_to_json(raw_header):

    lines = raw_header.splitlines()

    for line in lines:
        # 跳过空行
        if line.strip():
            # 将每行按照第一个冒号拆分为键和值
            key, value = line.split(":", 1)
            # 去除键和值的多余空白，并添加到字典中
            headers[key.strip()] = value.strip()

raw_header_to_json(raw_header)

