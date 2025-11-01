import sys, os, threading, io, qrcode, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
sys.path.append(os.path.abspath("./src"))

from operation import OperationService
from meituan import MeituanService
from douyin import DouyinService
from tools import loginservice
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode

def show_qr_terminal_from_png(png_bytes: bytes):
    # 解析二维码内容
    img = Image.open(BytesIO(png_bytes))
    decoded = decode(img)
    if not decoded:
        raise ValueError("无法解析二维码，请检查图像内容")

    data = decoded[0].data.decode("utf-8")

    # 重新生成二维码并在终端输出
    qr = qrcode.QRCode(border=1)  # 边框设小一点更适合终端
    qr.add_data(data)
    qr.make(fit=True)

    f = io.StringIO()
    qr.print_ascii(out=f, invert=True)  # invert 适合深色终端
    f.seek(0)
    print(f.read())
    return data  # 返回解码结果以备使用



# date=datetime(2025,10,16)
# date = datetime.now()-timedelta(days=1)
date = datetime.now()

def opworker():
    login = loginservice()
    # login.get_qrcode(login.get_uuid())
    # show_qr_terminal_from_png(login.qrcode.content)
    login.token_check()
    if not login.token:
        login.main_flow(show_qr_callback=show_qr_terminal_from_png)
    token = login.token
    op =  OperationService(date, token)
    return op.data.get('turnoverSumFee')
def mtworker():
    mt = MeituanService(date)
    return mt.data.get('meituan_total')
def dyworker():
    dy = DouyinService(date)
    return dy.data.get('douyin_total')

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(opworker): "op",
        executor.submit(mtworker): "mt",
        executor.submit(dyworker): "dy",
    }

    results = {}
    sum = 0
    for future in as_completed(futures):
        name = futures[future]
        sum += future.result()
        results[name] = future.result()

print(results)
#这个地方，业务逻辑应该是，必须有值，否则报空值异常
#sum = dy.data.get('douyin_total', 0) + mt.data.get('meituan_total', 0) + op.data.get('turnoverSumFee', 0)
#sum = round(sum, 2)
print(f"总营业额:{sum}")
