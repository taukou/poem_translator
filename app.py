from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import configparser
import os
import re
from utils.translator import translate_poem
from utils.emotion_analyzer import EmotionAnalyzer
from utils.speech_generator import generate_emotional_speech
from utils.gemini_translator import translate_and_analyze, analyze_poem_emotions, compare_poems

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# 讀取配置文件
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

API_KEY = config.get('API', 'api_key', fallback='your_api_key_here')
AZURE_KEY = config.get('AZURELANGUAGE', 'AZURE_LANGUAGE_KEY', fallback='your_azure_key_here')


def load_poems():
    """從唐詩三百首文本載入詩詞清單。"""
    poems_path = os.path.join(os.path.dirname(__file__), '唐詩三百首.txt')

    if not os.path.exists(poems_path):
        return []

    with open(poems_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    blocks = re.split(r'\n\s*\n', content)
    poems = []

    for idx, block in enumerate(blocks, start=1):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        poem = {'id': idx, 'title': '', 'author': '', 'style': '', 'text': ''}
        for line in lines:
            if line.startswith('詩名:'):
                poem['title'] = line.replace('詩名:', '', 1).strip()
            elif line.startswith('作者:'):
                poem['author'] = line.replace('作者:', '', 1).strip()
            elif line.startswith('詩體:'):
                poem['style'] = line.replace('詩體:', '', 1).strip()
            elif line.startswith('詩文:'):
                poem['text'] = line.replace('詩文:', '', 1).strip()

        if poem['title'] and poem['text']:
            poems.append(poem)

    return poems


POEMS = load_poems()


@app.route('/api/poems', methods=['GET'])
def list_poems():
    """取得唐詩三百首詩詞清單。"""
    return jsonify({'count': len(POEMS), 'poems': POEMS})


@app.route('/api/poems/<int:poem_id>', methods=['GET'])
def get_poem(poem_id):
    poem = next((p for p in POEMS if p['id'] == poem_id), None)
    if poem is None:
        return jsonify({'error': '找不到指定的詩詞'}), 404
    return jsonify(poem)


def translate_and_analyze_emotion(text, target_language='zh-Hant'):
    """Helper: translate text and run emotion analysis on the modern Chinese."""
    # 翻譯
    translation_result = translate_poem(text, target_language=target_language)

    # 情緒分析（針對白話文，使用簡體 zh-Hans 作為分析語言）
    analyzer = EmotionAnalyzer()
    modern_text = translation_result.get('modern_chinese', '')
    emotion_result = analyzer.analyze_emotion_with_details(modern_text, language='zh-Hans')

    return {
        'success': True,
        'translation': {
            'original': translation_result.get('original', text),
            'modern_chinese': modern_text,
            'target_language': translation_result.get('target_language', target_language),
            'translated': translation_result.get('translated', '')
        },
        'emotion_analysis': emotion_result
    }


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


@app.route('/api/translate-detailed', methods=['POST'])
def translate_detailed():
    """古詩詳細解釋API - 使用 Gemini API 提供內容解釋、詞語註釋和作者介紹
    
    請求示例:
    {
        "text": "昔日戲言身後事，今朝都到眼前來。",
        "target_language": "zh-Hant"
    }
    
    回覆包含:
    - content_explanation: 詳細解釋古詩的內容、意境和主旨
    - word_annotations: 詞語註釋（古文關鍵詞彙解釋）
    - author_introduction: 作者生平、時代背景和文學成就
    """
    data = request.get_json()
    text = data.get('text', '').strip()
    target_language = data.get('target_language', 'zh-Hant')  # 預設目標語言
    
    if not text:
        return jsonify({'error': '請輸入要解釋的古詩'}), 400
    
    try:
        result = translate_and_analyze(text, target_language)
        if result.get('error'):
            return jsonify(result), 502
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'古詩解釋失敗: {str(e)}'}), 500


@app.route('/api/analyze-poem-emotions', methods=['POST'])
def api_analyze_poem_emotions():
    """情感分析API - 使用 Gemini API 分析古詩的情感特徵"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': '請輸入要分析的文本'}), 400
    
    try:
        result = analyze_poem_emotions(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'情感分析失敗: {str(e)}'}), 500


@app.route('/api/compare-poems', methods=['POST'])
def api_compare_poems():
    """詩歌比較API - 使用 Gemini API 比較兩首詩的風格和特點"""
    data = request.get_json()
    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    
    if not text1 or not text2:
        return jsonify({'error': '請輸入兩首要比較的詩文'}), 400
    
    try:
        result = compare_poems(text1, text2)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'詩歌比較失敗: {str(e)}'}), 500


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
def translate_and_analyze_route():
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


@app.route('/api/generate-speech', methods=['POST'])
def generate_speech():
    """情感語音合成端點 - 根據情緒調整音調和語速"""
    data = request.get_json()
    
    # 接收前端傳來的參數，並設定預設值
    text = data.get('text', '').strip()
    emotion = data.get('emotion', '平')
    speed = float(data.get('speed', 1.0))
    pitch = float(data.get('pitch', 1.0))
    
    if not text:
        return jsonify({'error': '請輸入要轉換的文本'}), 400
        
    try:
        # 呼叫我們剛寫好的模組
        result = generate_emotional_speech(text, emotion, speed, pitch)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'語音合成失敗: {str(e)}'}), 500

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
