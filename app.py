from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import configparser
import os

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
    
    # 這裡添加你的翻譯邏輯
    # 例如調用Azure Translator或其他翻譯服務
    translated_text = f"[翻譯結果] {text}"
    
    return jsonify({
        'original': text,
        'translated': translated_text
    })


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
