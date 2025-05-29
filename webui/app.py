from flask import Flask, jsonify
import base64
from io import BytesIO

# 初始化 Flask 应用
app = Flask(__name__)



@app.route('/', methods=['get'])
def start():
    img_str = "a"

    return jsonify({"image": img_str})


if __name__ == '__main__':
    # 启动 Flask 应用，默认运行在 http://127.0.0.1:5000/
    print('aaa')
    app.run(debug=True, port=5001)
