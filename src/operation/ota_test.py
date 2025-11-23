from datetime import datetime
from src.operation.OTAUpdater import OTAUpdater
from src.tools import loginservice

from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
import qrcode,io
wkdate = datetime(2025,11,23)
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

login = loginservice()
# login.get_qrcode(login.get_uuid())
# show_qr_terminal_from_png(login.qrcode.content)
login.token_check()
if not login.token:
    login.main_flow(show_qr_callback=show_qr_terminal_from_png)
token = login.token

ota = OTAUpdater(data={}, date=wkdate, token=token)
ota.run()
print(ota.reponse)