import requests

from tqdm import tqdm
raw_header = """
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
Accept: application/json, text/plain, */*
Accept-Language: zh,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Priority: u=0
"""
headers = {}

lines = raw_header.splitlines()
for line in lines:
    # 跳过空行
    if line.strip():
        # 将每行按照第一个冒号拆分为键和值
        key, value = line.split(":", 1)
        # 去除键和值的多余空白，并添加到字典中
        headers[key.strip()] = value.strip()

url = 'https://software.download.prss.microsoft.com/dbazure/Win11_24H2_Chinese_Simplified_x64.iso?t=7eeabb55-6780-4008-bfea-122cd4c70613&P1=1743160991&P2=601&P3=2&P4=CpivamoDUD50jMcrBqJYeMc7FkmmjEmohwEfR7vyEF99MCBUcD4A1OuUdcuknM1llursk7u%2fxescJbFE%2fMs%2bOYr3%2byiX5N6weCzgnTWbGj0DJClCtrNRc5JABKxVxLxLAm88XZBr%2bmTCqhlEHjo4L%2b06%2fHO1AjaNe2ekFaoESFkyPTVf5rxI3AkyiuTAV67Fzb%2fy%2fvG9wEI9yT866g5jSiYxzYeWbepaM4VDjV3y5%2fggDqzeSqGHNmdNWauoLGphtHWJLpwPl5iFFPktnQTzEXqLFi51p%2bnpOqZHGp98YZfmFFUdNDvw7feJM9JrNFRL5BYdmRGi0Uw%2bCHp8QwnTjg%3d%3d'
#url = f"https://{headers['Host']}/{api_endpoint}"

local_filename = 'largefile.zip'  # 本地保存的文件名

def download_file(url, header, local_filename):
    # 发起 GET 请求，启用流式下载
    with requests.get(url, stream=True, headers=header) as response:
        response.raise_for_status()  # 检查请求是否成功
        total_size = int(response.headers.get('Content-Length', 0))
        # 使用 tqdm 显示进度条
        with open(local_filename, 'wb') as file, tqdm(
            desc=local_filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            # 分块下载文件
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    progress_bar.update(len(chunk))
    print(f"文件已成功下载并保存为 {local_filename}")

if __name__ == '__main__':
    download_file(url=url, header=headers,local_filename=local_filename)

