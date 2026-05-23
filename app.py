from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import configparser
import os
from utils.translator import translate_poem
from utils.emotion_analyzer import EmotionAnalyzer

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


@app.route('/api/analyze-emotion', methods=['POST'])
def analyze_emotion():
    """情緒分析API - 分析文本的情緒和意見"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': '請輸入要分析的文本'}), 400
    
    try:
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion_with_details(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'情緒分析失敗: {str(e)}'}), 500


def translate_and_analyze_emotion(text, target_language='zh-Hant'):
    """翻譯並分析情緒 - 將古文翻譯並分析其情緒"""
    # 步驟1: 翻譯文本
    translation_result = translate_poem(text, target_language)
    
    # 步驟2: 分析翻譯後的文本情緒
    analyzer = EmotionAnalyzer()
    emotion_result = analyzer.analyze_emotion_with_details(translation_result['modern_chinese'])
    
    # 合併結果
    return {
        'original': translation_result['original'],
        'modern_chinese': translation_result['modern_chinese'],
        'target_language': translation_result['target_language'],
        'translated': translation_result['translated'],
        'emotion': emotion_result
    }


@app.route('/api/translate-and-analyze', methods=['POST'])
def translate_and_analyze():
    """翻譯並分析情緒API - 將古文翻譯並分析其情緒"""
    data = request.get_json()
    text = data.get('text', '').strip()
    target_language = data.get('target_language', 'zh-Hant')
    
    if not text:
        return jsonify({'error': '請輸入要翻譯的文本'}), 400
    
    try:
        result = translate_and_analyze_emotion(text, target_language)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'翻譯和分析失敗: {str(e)}'}), 500


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
