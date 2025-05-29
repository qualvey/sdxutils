from flask import Flask, render_template, jsonify, session
import base64
from flask_cors import CORS

from tools import env, logger
import requests
import json
import random


logger  =  logger.get_logger(__name__)

# 初始化 Flask 应用
app = Flask(__name__)
app.secret_key = 'sdjadio1u80u09213902ihbv$wi90i01'

CORS(app)

@app.route('/', methods=['get'])
def start():
    return render_template('./webui/index.html')

@app.route('/nothing', methods=['get'])
def nothitng():
    print('login get')
    uuid = session.get('uuid')
    if not uuid:
        logger.error('no uuid transport')
    logger.error("Got the uid!")
    return jsonify({'uuid': uuid})

if __name__ == '__main__':
    # 启动 Flask 应用，默认运行在 http://127.0.0.1:5000/
    print('aaa')
    app.run(debug=True, port=5001)
