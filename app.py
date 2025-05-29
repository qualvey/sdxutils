from flask import Flask, jsonify, session, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import base64
from io import BytesIO, StringIO
from PIL import Image
from flask_cors import CORS

from tools import env, logger
import xml.etree.ElementTree as ET
import os

import re
import requests
import time
import json
from datetime import datetime, timezone, date, timedelta
import pytz

from meituan.main import get_meituanSum
from douyin.main    import  get_douyinSum

logger  =  logger.get_logger(__name__)

# 初始化 Flask 应用
app = Flask(__name__, template_folder='./webui')
app.secret_key = 'sdjadio1u80u09213902ihbv$wi90i01'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

raw_request_get_id = ''' GET /connect/qrconnect?appid=wx5322e698d6ac98d4&scope=snsapi_login&redirect_uri=http%3A%2F%2Fsso.cloudnetcafe.com%2F%23%2FbindingAccount&state=25750&login_type=jssdk&self_redirect=false&styletype=&sizetype=&bgcolor=&rst=&style=black&href=https://hub.sdxnetcafe.com/src/static/wxlogin.css&f=xml&1743032985484&_=1743032647062 HTTP/2
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: cors
Connection: keep-alive
Host: open.weixin.qq.com
Accept: application/xml, text/xml, */*; q=0.01
Accept-Language: zh,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate, br, zstd
X-Requested-With: XMLHttpRequest
Referer: https://open.weixin.qq.com/connect/qrconnect?appid=wx5322e698d6ac98d4&scope=snsapi_login&redirect_uri=http%3A%2F%2Fsso.cloudnetcafe.com%2F%23%2FbindingAccount&state=25750&login_type=jssdk&self_redirect=false&styletype=&sizetype=&bgcolor=&rst=&style=black&href=https://hub.sdxnetcafe.com/src/static/wxlogin.css
Sec-Fetch-Dest: empty
Priority: u=0
'''

def parse_raw_request(raw_request):
    #解析原始请求头，不用管
    # 使用 StringIO 将原始请求字符串转换为文件对象，方便逐行读取
    request_file = StringIO(raw_request)
    # 读取请求行（例如：GET /connect/qrcode/061p2Za447CUkl2X HTTP/2）
    request_line = request_file.readline().strip()
    # 使用正则表达式解析请求行
    match = re.match(r'(\S+) (\S+) (\S+)', request_line)
    if match:
        method, path, _ = match.groups()
    else:
        raise ValueError("无法解析请求行")
    # 读取头部信息并构建 headers 字典
    headers = {}
    for line in request_file:
        line = line.strip()
        if not line:
            break  # 空行表示头部结束
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()
    return method, path, headers

def send_raw_request(raw_request):
    method, path, headers = parse_raw_request(raw_request)
    # 构建完整的 URL
    #url = f'https://open.weixin.qq.com{path}'
    url = f'http://{headers['Host']}{path}'

    # 发送请求
    response = requests.request(method, url, headers=headers)
    return response

def get_uuid():
    response = send_raw_request(raw_request_get_id)
    xml_data = response.text
    root = ET.fromstring(xml_data)
    uuid = root.find('uuid').text
    if not uuid:
        prit('uuid error~!!')
    return uuid

def show_img(response_qrcode):
    image = Image.open(BytesIO(response_qrcode.content))
        # 显示图片
    image.show()

def get_qrcode(uuid):
    raw_request_qrcode = f''' GET /connect/qrcode/{uuid} HTTP/2
    Host: open.weixin.qq.com
    User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
    Accept: image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5
    Accept-Language: zh,en-US;q=0.7,en;q=0.3
    Accept-Encoding: gzip, deflate, br, zstd
    Connection: keep-alive
    Referer: https://open.weixin.qq.com/connect/qrconnect?appid=wx5322e698d6ac98d4&scope=snsapi_login&redirect_uri=http%3A%2F%2Fsso.cloudnetcafe.com%2F%23%2FbindingAccount&state=62245&login_type=jssdk&self_redirect=false&styletype=&sizetype=&bgcolor=&rst=&style=black&href=https://hub.sdxnetcafe.com/src/static/wxlogin.css
    Sec-Fetch-Dest: image
    Sec-Fetch-Mode: no-cors
    Sec-Fetch-Site: same-origin
    Priority: u=5, i
    TE: trailers'''

    response_qrcode = send_raw_request(raw_request_qrcode)
    return response_qrcode

def lp_wxcode(uuid, max_attempts=10, interval=1):
    #响应载荷格式：window.wx_errcode=405;window.wx_code='011H1G000wIeYT1NwR300yrNXp2H1G0W';

    for attempt in range(max_attempts):
        timestamp_ms = int(time.time() * 1000)

        raw_request_wxcode = f'''GET /connect/l/qrconnect?uuid={uuid}&last=404&_={timestamp_ms} HTTP/1.1
        Host: lp.open.weixin.qq.com
        User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
        Accept: */*
        Accept-Language: zh,en-US;q=0.7,en;q=0.3
        Accept-Encoding: gzip, deflate, br, zstd
        Connection: keep-alive
        Referer: https://open.weixin.qq.com/
        Sec-Fetch-Dest: script
        Sec-Fetch-Mode: no-cors
        Sec-Fetch-Site: same-site'''
        response = send_raw_request(raw_request_wxcode)
        if response.status_code == 200:
                    errcode_match = re.search(r"window\.wx_errcode=(\d+);", response.text)
                    code_match = re.search(r"window\.wx_code='(.*?)';", response.text)
                    if errcode_match:
                        errcode = int(errcode_match.group(1))
                        if errcode == 405 and code_match:
                            wx_code = code_match.group(1)
                            print(f"获取到 wx_code: {wx_code}")
                            return wx_code

        time.sleep(interval)

def get_token(wx_code):
    raw_request_token = f'''POST /api/admin/user/wechatLogin?code={wx_code} HTTP/1.1
    Host: sso.cloudnetcafe.com
    User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0
    Accept: application/json, text/plain, */*
    Accept-Language: zh,en-US;q=0.7,en;q=0.3
    Accept-Encoding: gzip, deflate
    Authorization: null
    Origin: http://sso.cloudnetcafe.com
    Connection: keep-alive
    Referer: http://sso.cloudnetcafe.com/
    Content-Length: 0'''

    response_token = send_raw_request(raw_request_token)
    with open(f'{env.proj_dir}/temp/tokenresponse.json', 'w') as f:
        json.dump(response_token.json(), f)

    logger.debug(f'token:{response_token.json()}')
    token = response_token.json().get('data')
    if token:
        return token
    else:
        logger.error('get token failed!')

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

def is_token_valid(data):
    '''
    data<String>-decoded token
    '''
    #返回两个值，bool和token（如果有
    #with open(f'{env.proj_dir}/temp/token.json', 'r') as cache:
    #    data = json.load(cache)

    exp_timestamp = data.get('exp')
    token = data.get('token')
    if exp_timestamp:
        # 将时间戳转换为 datetime 对象
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        # 获取当前 UTC 时间
        current_datetime = datetime.utcnow()
        # 比较过期时间与当前时间
        if exp_datetime > current_datetime:
            return True ,token
        else:
            return False 
    else:
        print("未找到过期时间")
        return False

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

# 启用 CORS
CORS(app, origins=['http://localhost:5173'])

from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 示例用户数据
users = {
    'sdx': User(2, 'sdx', generate_password_hash('passwd'))
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == int(user_id):
            return user
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username].check_password(password):
            user = users[username]
            login_user(user)
            flash('登录成功！')
            return redirect(url_for('home'))
        else:
            error = '无效的用户名或密码'
    return render_template('login.html', error=error)

@app.route('/home', methods=['get'])
@login_required
def home():
    uuid = session.get('uuid')
    if not uuid:
        # 如果没有 uuid，生成一个新的 uuid 并保存在 session 中
        uuid = get_uuid()  # 假设 get_uuid() 用来生成唯一的 uuid
        session['uuid'] = uuid  # 将 uuid 存入 session 中
        return render_template('index.html')
    logger.info('uuid存在，返回dashboard')
    return render_template('dashboard.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/', methods=['get'])
def start():
    return render_template('login.html')

@app.route('/qrcode', methods=['get'])

@login_required
def qrcode():
    uuid = session.get('uuid')
    logger.info(f'uuid:{uuid}')
    response_qrcode = get_qrcode(uuid=uuid)
    image = Image.open(BytesIO(response_qrcode.content))
    # 将图像转换为 Base65 字符串
    img_str = image_to_base64(image)
    return jsonify({"image": img_str})

@app.route('/login_state', methods=['get'])
@login_required
def get_login_state():
    print('login get')
    uuid = session.get('uuid')
    if session.get('token'):
        return jsonify({'token': "tokenget"})
    else:
        while True:
            wx_code = lp_wxcode(uuid=uuid)
            session['wx_code'] = wx_code
            token = get_token(wx_code)
            if token:
                session['token'] = token
                logger.debug(f'token:{token}')
                return jsonify({'token': 'token getted.'})

@app.route('/mtdata', methods=['get'])
@login_required
def meituan():

    date = request.args.get('date')
    if date != None:
        date = datetime.strptime(date, '%Y-%m-%d')
    else:
        date = datetime.today()
        date = date - timedelta(days=1)
    data = get_meituanSum(date)
    logger.info(f'gettting meituan data, date:{date},value:{data}')
    logger.debug(data.__class__)
    return jsonify(data)

@app.route('/dydata', methods=['get'])
def douyin():

    date = request.args.get('date')
    if date != None:
        date = datetime.strptime(date, '%Y-%m-%d')
    else:
        date = datetime.today()
        date = date - timedelta(days=1)
    dydata = get_douyinSum(date)
    logger.info(f'gettting douyin data , get{dydata}')
    logger.debug(dydata.__class__)
    if  dydata is None:
        return jsonify({'dy': 0})
    else:
        return jsonify({'dy': dydata})
    return jsonify({'dy': dydata})

@app.route('/logout')
@login_required
def logout():
    logout_user()  # 清除用户的会话
    session.pop('uuid', None)
    session.pop('wx_code', None)
    session.pop('token', None)
    flash('您已成功退出登录！')  # 提示用户已退出
    return redirect(url_for('login'))  # 重定向到登录页

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
    token = session.get('token')
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

@app.route('/operation', methods=['GET'])
@login_required
def fetch_operation_data():
    headers = get_headers()
    date  = request.args.get('date')
    branchId = "a92fd8a33b7811ea87766c92bf5c82be"
    state =     f"/api/statistics/branch/operation/data/state?branchId={branchId}&startTm={date}+00:00:00"
    
    #url = f"https://{headers['Host']}{API_ENDPOINTS['state']}"
    url = f"https://{headers['Host']}{state}"
    response = requests.get(url, headers=headers, timeout=10)
    response_data = response.json()
    if response.status_code == 200 and 'data' in response_data:
        data = response_data['data']  # 将 JSON 响应保存到字典中
    income = data['turnoverSumFee']
    return jsonify({'income': income})
@app.route('/run' ,methods=['GET'])
@login_required
def run():
    uuid = session.get('uuid')
    wx_code = session.get('wx_code')
    token = session.get('token')
    token_json = decode_jwt_without_verification(token)
    tokenvalid = is_token_valid(token_json)
    logger.debug(f'this is token valid check:{tokenvalid}')
    return str(tokenvalid)

@app.route('/test', methods=['GET'])
def test():
    date = request.args.get('date')
    logger.debug(f'get parameters:{date}')
    return jsonify({'data': 'nothing'})

if __name__ == '__main__':
    # 启动 Flask 应用，默认运行在 http://127.0.0.1:5000/
    app.run(debug=True, port=5001)
