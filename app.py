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
config.read('config.ini', encoding='utf-8')

API_KEY = config.get('API', 'api_key', fallback='your_api_key_here')
AZURE_KEY = config.get('AZURELANGUAGE', 'AZURE_LANGUAGE_KEY', fallback='your_azure_key_here')


@app.route('/')
def index():
    """主頁路由"""
    return render_template('index.html')


@app.route('/api/translate', methods=['POST'])
def translate():
    """翻譯API - 將古文翻譯為現代中文"""
    data = request.get_json()
    text = data.get('text', '').strip()
    target_language = data.get('target_language', 'zh-Hant')  # 預設目標語言
    
    if not text:
        return jsonify({'error': '請輸入要翻譯的文本'}), 400
    
    try:
        result = translate_poem(text, target_language)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'翻譯失敗: {str(e)}'}), 500


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
    # ===== 測試模式 =====
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("\n" + "="*60)
        print("🧪 開始測試: 翻譯 + 情緒分析")
        print("="*60 + "\n")
        
        # 假輸入 - 古詩
        test_poem = "昔日戲言身後事，今朝都到眼前來。"
        
        print(f"📖 原始古詩：{test_poem}\n")
        
        try:
            # 步驟1: 翻譯
            print("📝 步驟1: 翻譯古詩...")
            print("-" * 60)
            translation_result = translate_poem(test_poem, target_language="zh-Hant")
            
            print(f"原始文言文：{translation_result['original']}")
            print(f"白話中文：{translation_result['modern_chinese']}")
            print(f"目標語言：{translation_result['target_language']}")
            print(f"翻譯結果：{translation_result['translated']}\n")
            
            # 步驟2: 對翻譯結果進行情緒分析
            print("😊 步驟2: 分析翻譯文本的情緒...")
            print("-" * 60)
            
            analyzer = EmotionAnalyzer()
            modern_text = translation_result['modern_chinese']
            
            emotion_result = analyzer.analyze_emotion_with_details(modern_text)
            
            if emotion_result:
                print(f"\n整體情緒：{emotion_result['overall_sentiment']}")
                print(f"情緒分數：{emotion_result['overall_scores']}")
                print(f"句子數量：{emotion_result['sentences_count']}\n")
                
                print("逐句分析結果：")
                print("-" * 60)
                for sentence in emotion_result['sentences']:
                    print(f"句子 {sentence['index']}: {sentence['text']}")
                    print(f"  情緒: {sentence['sentiment']}")
                    print(f"  分數: {sentence['scores']}")
                    if sentence['opinions']:
                        print(f"  意見: {sentence['opinions']}")
                    print()
            
            print("="*60)
            print("✅ 測試完成！")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        # 正常運行模式
        app.run(debug=True, host='0.0.0.0', port=5000)
