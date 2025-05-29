import sys
from PyQt6 import QtWidgets, QtGui
from PIL import Image
from io import BytesIO

class QRCodeWindow(QtWidgets.QWidget):
    def __init__(self, img_data):
        super().__init__()
        self.setWindowTitle("qrcode")
        self.setFixedSize(320, 340)  # 固定窗口大小

        # 用PIL打开图片
        pil_img = Image.open(BytesIO(img_data)).convert("RGB")
        pil_img = pil_img.resize((300, 300))

        # PIL转Qt图像
        data = pil_img.tobytes("raw", "RGB")
        qimg = QtGui.QImage(data, 300, 300, QtGui.QImage.Format.Format_RGB888)

        pixmap = QtGui.QPixmap.fromImage(qimg)

        # 标签显示图片
        label = QtWidgets.QLabel(self)
        label.setPixmap(pixmap)
        label.setGeometry(10, 10, 300, 300)  # 图片位置和大小

def main(img_data):
    app = QtWidgets.QApplication(sys.argv)
    win = QRCodeWindow(img_data)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    # 这里测试用文件读取，换成你的二维码字节数据
    with open("qrcode.jpeg", "rb") as f:
        data = f.read()
    main(data)

