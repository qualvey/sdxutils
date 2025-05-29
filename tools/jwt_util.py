
import jwt
from tools.login import token
import base64
import json
from datetime import datetime, timezone
import pytz

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

# 示例使用
if __name__ == "__main__":
    try:
        decoded_data = decode_jwt_without_verification(token)
        print(f"JWT 载荷: {decoded_data}")
        print(f"过期时间: {decoded_data['exp_readable']}")
    except ValueError as e:
        print(f"错误: {e}")
