from flask import Flask, render_template, request, jsonify
from tools import loginservice,LoggerService
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = LoggerService(__name__).logger
app = Flask(__name__)
login = loginservice()

def main_flow():
    uuid = login.get_uuid()
    if not uuid:
        logger.error('main_flow 停止：未获得 uuid')
        return None
    response_qrcode = login.get_qrcode(uuid=uuid)
    return response_qrcode

@app.route('/')
def index():
    qrcode = main_flow()
    return render_template('index.html', qrcode=qrcode) 

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({'status': 'success', 'message': 'API is working'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)