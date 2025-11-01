
from .logger import LoggerService
logger = LoggerService(__name__).logger
import xml.etree.ElementTree as ET

import re, requests, sys, time, base64, json, pytz, os
from datetime import datetime, timezone

#配置存放位置，pyinstaller打包和源码运行时不一样
# 配置存放位置，兼容源码运行和 PyInstaller exe
def get_proj_dir():
    if getattr(sys, 'frozen', False):  
        # 打包后的 exe 运行
        return os.path.dirname(sys.executable)
    else:
        # 源代码运行
        # return os.path.dirname(os.path.abspath(__file__))
        return os.getcwd()


proj_dir = get_proj_dir()
temp_dir = os.path.join(proj_dir, "temp")
cache_file = os.path.join(temp_dir, "token.json")
os.makedirs(temp_dir, exist_ok=True)  # 确保 temp 目录存在
WINDOW_NAME = "QR Code Viewer"

class loginservice:
    def __init__(self, auto_login: bool = True):
        self.uuid = '' 
        self.qrcode = object
        self.token = ''
        """
        登录服务逻辑类。

        参数:
        auto_login: 是否在构造时自动执行完整的扫码登录流程（默认 True，以兼容现有导入处）。
                    GUI 程序应传入 False 并手动调用 main_flow，传入显示回调。
        """
        self.cache_check()

        logger.info('loginservice  initialized')
        # if self.cache_check(cache_file=cache_file):
        #     logger.info('缓存登录成功')
        # else:
        #     if auto_login:
        #         token = self.main_flow(cache_file=cache_file)
        #         if token:
        #             self.token = token
        #             logger.info('扫码登录成功')
        #         else:
        #             logger.error('扫码登录失败')
 
    def cache_check(self,cache_file: str = f'{temp_dir}/token.json'):
        if os.path.isfile(cache_file):
            logger.info('token文件存在')
            status, token = self.token_check()
            logger.info(f'token状态: {status}')
            if status:
                logger.info("令牌未过期,不用扫码")
                self.token = token
                return True
            else:
                logger.info('token过期')
                return False
        else:
            logger.info('token文件不存在')
            return False

    def get_uuid(self):
        logger.info('获取 uuid 中...')
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
        url = f"http://{headers['Host']}{api_endpoint}"
        try:
            logger.debug(f'get_uuid 请求 URL: {url} 参数: {params}')
            response = requests.get(url=url, params=params, headers=headers)
            xml_data = response.text
            root = ET.fromstring(xml_data)
            elem = root.find('uuid')
            uuid = elem.text if elem is not None else None
            if not uuid:
                logger.error('uuid error~!! xml response missing <uuid> element')
                logger.debug(f'uuid xml payload: {xml_data}')
            else:
                logger.debug(f'get_uuid -> {uuid}')
            self.uuid = uuid
            return uuid
        except Exception as e:
            logger.warning(f'get_uuid 请求或解析失败: {e}')
            return None

    # GUI 相关功能已移除：login 模块仅负责网络/令牌逻辑。
    # 如果需要在 GUI 中显示二维码，请调用 main_flow 时传入 show_qr_callback(bytes)
    # 和 close_qr_callback()。

    def get_qrcode(self,uuid):
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
        try:
            response_qrcode = requests.get(url=url, headers=headers)
            # log for debugging
            try:
                ct = response_qrcode.headers.get('Content-Type')
            except Exception:
                ct = None
            logger.debug(f'get_qrcode status={response_qrcode.status_code} content-type={ct} len={len(response_qrcode.content) if response_qrcode.content else 0}')
            self.qrcode = response_qrcode
            return response_qrcode
        except Exception as e:
            logger.warning(f'get_qrcode 请求失败: {e}')
            return None

    def lp_wxcode(self,uuid, max_attempts=10, interval=1):
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

    def get_token(self,wx_code):
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

    def decode_jwt_without_verification(self,token):
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

    def main_flow(self, cache_file: str = f'{temp_dir}/token.json',
                  show_qr_callback=None, close_qr_callback=None):
        """
        执行扫码登录主流程（网络 & 令牌处理），但不直接负责显示二维码。

        参数:
        cache_file: 缓存 token 的文件路径。
        show_qr_callback: 可选回调，接收二维码图片的 bytes 内容，GUI 层应在主线程中显示它。
        close_qr_callback: 可选回调，登录成功时调用以关闭二维码显示。

        返回:
        token 字符串或 None
        """
        logger.info('开始扫码登录,')
        logger.info(f'qr code 显示回调: {"已提供" if show_qr_callback else "未提供"}')
        uuid = self.get_uuid()
        if not uuid:
            logger.error('main_flow 停止：未获得 uuid')
            return None
        response_qrcode = self.get_qrcode(uuid=uuid)

        # 将二维码内容交给上层 GUI 回调处理；若无回调则保存为临时文件并记录路径
        try:
            qr_bytes = response_qrcode.content if response_qrcode is not None else None
        except Exception:
            qr_bytes = None

        logger.debug(f'main_flow: qr_bytes length = {len(qr_bytes) if qr_bytes else 0}')

        if show_qr_callback and qr_bytes:
            try:
                logger.debug('调用 show_qr_callback 显示二维码')
                show_qr_callback(qr_bytes)
            except Exception as e:
                logger.warning(f"执行 show_qr_callback 时出错: {e}")
        else:
            # headless fallback: 写到临时文件，便于用户手动打开查看
            try:
                qr_path = os.path.join(temp_dir, f'qr_{uuid}.png')
                with open(qr_path, 'wb') as f:
                    f.write(qr_bytes or b'')
                logger.info(f"二维码已保存到: {qr_path}")
            except Exception as e:
                logger.warning(f"保存二维码临时文件失败: {e}")

        wx_code = self.lp_wxcode(uuid=uuid)
        token = None
        if wx_code:
            token = self.get_token(wx_code)

        if token:
            self.token = token
            # 通知 GUI 关闭二维码显示（如果有）
            if close_qr_callback:
                try:
                    close_qr_callback()
                except Exception as e:
                    logger.warning(f"执行 close_qr_callback 时出错: {e}")

            token_json = self.decode_jwt_without_verification(token)
            token_json['token'] = token
            try:
                with open(cache_file, 'w') as cache:
                    json.dump(token_json, cache)
            except Exception as e:
                logger.warning(f"写入 token 缓存失败: {e}")
            return token
        else:
            return None

    def token_check(self,cache_file: str = f'{temp_dir}/token.json'):
        print('检查 token 状态...')
        print(f'cache_file: {cache_file}')
    
        #返回两个值，bool和token（如果有
        with open(cache_file, 'r') as cache:
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
                self.token = token
                return True, token
            else:
                return False, 'token已过期'
        else:
            logger.error('未找到过期时间')
            return False, '未找到过期时间'
