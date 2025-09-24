
from io import StringIO
from tools import env, logger
from PIL import Image
from io import BytesIO
import xml.etree.ElementTree as ET
import os

import re
import requests
import time
import base64
import json
import cv2
import numpy as np 

from datetime import datetime, timezone
import pytz
from tools.env import proj_dir


logger = logger.get_logger(__name__)
WINDOW_NAME = "QR Code Viewer"

def get_uuid():

    api_endpoint = "/connect/qrconnect"
    params =  {
    "appid" : "wx5322e698d6ac98d4",
    "scope" : "snsapi_login",
#"redirect_uri" : "http%3A%2F%2Fsso.cloudnetcafe.com%2F%23%2FbindingAccount",,
    "redirect_uri" : "http://sso.cloudnetcafe.com/#/bindingAccount",
    "state" : "25750",
    "login_type" : "jssdk",
    "self_redirect" : "false",
    "styletype" : None,
    "sizetype" : None,
    "`bgcolor" : None,
    "rst" : None,
    "style" : "black",
    "href" : "https://hub.sdxnetcafe.com/src/static/wxlogin.css",
    "f" : "xml",
    #"1743032985484",
    "_" : "1743032647062" ,
    }
    headers = {
    "Host" : "open.weixin.qq.com",
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept" : "application/xml, text/xml, */*; q=0.01",
    "Accept-Language" : "zh,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding" : "gzip, deflate, br, zstd",
    "X-Requested-With" : "XMLHttpRequest",
    "Connection" : "keep-alive",
    "Referer" : "https://open.weixin.qq.com/connect/qrconnect?appid=wx5322e698d6ac98d4&scope=snsapi_login&redirect_uri=http%3A%2F%2Fsso.cloudnetcafe.com%2F%23%2FbindingAccount&state=25750&login_type=jssdk&self_redirect=false&styletype=&sizetype=&bgcolor=&rst=&style=black&href=https://hub.sdxnetcafe.com/src/static/wxlogin.css",
    "Sec-Fetch-Dest" : "empty",
    "Sec-Fetch-Mode" : "cors",
    "Sec-Fetch-Site" : "same-origin",
    "Priority" : "u=0"
    }

    url = f'http://{headers['Host']}{api_endpoint}'

    response = requests.get(url=url, params=params, headers=headers)
    xml_data = response.text
    root = ET.fromstring(xml_data)
    uuid = root.find('uuid').text
    if not uuid:
        logger.error('uuid error~!!')
    return uuid

def show_img(response_qrcode):
    arr = np.asarray(bytearray(response_qrcode.content), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    # 设置窗口和图像大小
    target_width, target_height = 300, 300
    resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)

    # 设置浮动窗口（可调大小 + 置顶 + 不变形）
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)  # WINDOW_AUTOSIZE 使窗口紧贴图像尺寸
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_TOPMOST, 1)

    # 显示缩放后的图像
    cv2.imshow(WINDOW_NAME, resized_img)
    cv2.waitKey(1)

def close_img():
    cv2.destroyWindow(WINDOW_NAME)

def get_qrcode(uuid):
    api_endpoint = f"/connect/qrcode/{uuid}"

    headers = {
    "Host" : "open.weixin.qq.com",
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept" : "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
    "Accept-Language" : "zh,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding" : "gzip, deflate, br, zstd",
    "Connection" : "keep-alive",
    "Referer" : "https://open.weixin.qq.com/connect/qrconnect?appid=wx5322e698d6ac98d4&scope=snsapi_login&redirect_uri=http%3A%2F%2Fsso.cloudnetcafe.com%2F%23%2FbindingAccount&state=62245&login_type=jssdk&self_redirect=false&styletype=&sizetype=&bgcolor=&rst=&style=black&href=https://hub.sdxnetcafe.com/src/static/wxlogin.css",
    "Sec-Fetch-Dest" : "image",
    "Sec-Fetch-Mode" : "no-cors",
    "Sec-Fetch-Site""" : "same-origin",
    "Priority" : "u=5, i",
    "TE" : "trailers"
    }
    url = f"https://{headers['Host']}{api_endpoint}"

    #response_qrcode = send_raw_request(raw_request_qrcode)
    response_qrcode = requests.get(url=url, headers = headers )
    return response_qrcode

def lp_wxcode(uuid, max_attempts=10, interval=1):
    #响应载荷格式：window.wx_errcode=405;window.wx_code='011H1G000wIeYT1NwR300yrNXp2H1G0W';

    for attempt in range(max_attempts):
        timestamp_ms = int(time.time() * 1000)
        api_endpoint  = f"/connect/l/qrconnect?uuid={uuid}" 
        params = {
            "last" :  "404",
            "_"    :  f"{timestamp_ms}"
        }

        headers = {
        "Host" : "lp.open.weixin.qq.com",
        "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept" : "*/*",
        "Accept-Language" : "zh,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding" : "gzip, deflate, br, zstd",
        "Connection" : "keep-alive",
        "Referer" : "https://open.weixin.qq.com/",
        "Sec-Fetch-Dest" : "script",
        "Sec-Fetch-Mode" : "no-cors",
        "Sec-Fetch-Site" : "same-site"
        }
        url = f"https://{headers['Host']}{api_endpoint}"
        
        response = requests.get(url=url, params=params, headers=headers)

        if response.status_code == 200:
                    errcode_match = re.search(r"window\.wx_errcode=(\d+);", response.text)
                    code_match = re.search(r"window\.wx_code='(.*?)';", response.text)
                    if errcode_match:
                        errcode = int(errcode_match.group(1))
                        if errcode == 405 and code_match:
                            wx_code = code_match.group(1)
                            logger.info(f"获取到 wx_code: {wx_code}")
                            return wx_code
        time.sleep(interval)

def get_token(wx_code):

    logger.debug(f'wx_code: {wx_code}')

    api_endpoint = f"/api/admin/user/wechatLogin"

    param = {
        "code" : f"{wx_code}"
        }

    headers = {
    "Host" : "sso.cloudnetcafe.com",
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept" : "application/json, text/plain, */*",
    "Accept-Language" : "zh,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding" : "gzip, deflate",
    "Authorization" : "null",
    "Origin" : "http://sso.cloudnetcafe.com",
    "Connection" : "keep-alive",
    "Referer" : "http://sso.cloudnetcafe.com/",
    "Content-Length" : "0",
            }
    url=f"http://{headers['Host']}{api_endpoint}"

    #response_token = send_raw_request(raw_request_token)
    response_token = requests.post(url=url, params=param, headers=headers)
    token = response_token.json()['data']
    return token

def decode_jwt_without_verification(token):
    """
    解码 JWT 并获取其过期时间（不验证签名）。

    参数:
    token (str): JWT 字符串。

    返回:
    dict: 包含 JWT 载荷和过期时间的字典。
    """
    try:
        # 拆分 JWT，获取头部、载荷和签名
        header, payload, signature = token.split('.')
        
        # Base64URL 解码载荷
        padded_payload = payload + '=' * (-len(payload) % 4)  # 修正填充
        decoded_payload = base64.urlsafe_b64decode(padded_payload)
        payload_data = json.loads(decoded_payload)

        # 获取过期时间戳
        exp_timestamp = payload_data.get('exp')
        if exp_timestamp is None:
            raise ValueError("JWT 中未包含 'exp' 声明。")
        
        # 将时间戳转换为可读格式
        #
        tz = pytz.timezone('Asia/Shanghai')  # 东八区时区
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=tz)
        payload_data['exp_readable'] = exp_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')

        return payload_data
    except Exception as e:
        raise ValueError(f"解码 JWT 时出错: {e}")

def return_qrcode():
    uuid = get_uuid()
    response_qrcode = get_qrcode(uuid=uuid)
    #show_img(response_qrcode)
    return response_qrcode

def main_flow():
    uuid = get_uuid()
    response_qrcode = get_qrcode(uuid=uuid)
    show_img(response_qrcode)
    wx_code = lp_wxcode(uuid=uuid)
    token = get_token(wx_code)
    if token:
       close_img() 
    token_json = decode_jwt_without_verification(token)
    token_json['token'] = token
    import sys
    # cache_file = os.path.join(os.path.dirname(sys.executable), "token.json")

    cache_file = f"{proj_dir}/temp/token.json"
    with open(cache_file, 'w') as cache:
        json.dump(token_json, cache)

def is_token_valid():
    #返回两个值，bool和token（如果有
    with open(f'{env.proj_dir}/temp/token.json', 'r') as cache:
        data = json.load(cache)

    exp_timestamp = data.get('exp')
    token = data.get('token')
    if exp_timestamp:
        # 将时间戳转换为 datetime 对象
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        # 获取当前 UTC 时间
        current_datetime = datetime.now(timezone.utc)
        # 比较过期时间与当前时间
        if exp_datetime > current_datetime:
            return True, token
        else:
            return False, None
    else:
        print("未找到过期时间")
        return False, None

if os.path.isfile(f'{env.proj_dir}/temp/token.json'):
    status, token = is_token_valid()
    if status:
        token = token
        logger.info("令牌未过期,不用扫码")
    else:
        token = main_flow()
        logger.info("令牌已过期")
else:
    token = main_flow()

