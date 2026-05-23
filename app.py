from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import configparser
import os
from utils.translator import translate_poem

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# 讀取配置文件
config = configparser.ConfigParser()
config.read('config.ini')

API_KEY = config.get('API', 'api_key', fallback='your_api_key_here')
AZURE_KEY = config.get('AZURE', 'azure_key', fallback='your_azure_key_here')


@app.route('/')
def index():
    """主頁路由"""
    return render_template('index.html')


@app.route('/api/translate', methods=['POST'])
def translate():
    """翻譯API"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': '請輸入要翻譯的文本'}), 400
    
    try:
        req_target = data.get('target_language') or 'de'
        result = translate_poem(text, target_language=req_target)
        return jsonify({
            'original': result.get('original', text),
            'modern_chinese': result.get('modern_chinese', ''),
            'target_language': result.get('target_language', ''),
            'translated': result.get('translated', '')
        })
    except Exception as e:
        return jsonify({'error': '翻譯服務發生錯誤'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康檢查"""
    return jsonify({'status': 'ok'})


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '資源未找到'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服務器內部錯誤'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
