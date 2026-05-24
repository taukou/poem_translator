import os
import time
import configparser
import re
from xml.sax.saxutils import escape as xml_escape

import azure.cognitiveservices.speech as speechsdk
from utils.emotion_analyzer import EmotionAnalyzer

config = configparser.ConfigParser()
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
config_path = os.path.join(project_root, 'config.ini')
config.read(config_path, encoding='utf-8')

SPEECH_KEY = os.getenv('SPEECH_KEY', config.get('AzureSpeech', 'SPEECH_KEY', fallback=''))
SPEECH_REGION = os.getenv('SPEECH_REGION', config.get('AzureSpeech', 'SPEECH_REGION', fallback=''))

SENTIMENT_STYLE_MAP = {
    "positive": "cheerful",
    "neutral": "general",
    "negative": "sad",
}


def _normalize_sentiment(value):
    """Normalize common sentiment labels to positive/neutral/negative."""
    if not value:
        return "neutral"

    label = str(value).strip().lower()
    alias_map = {
        "positive": "positive",
        "neutral": "neutral",
        "negative": "negative",
        "pos": "positive",
        "neu": "neutral",
        "neg": "negative",
        "喜": "positive",
        "樂": "positive",
        "快樂": "positive",
        "平": "neutral",
        "中性": "neutral",
        "悲": "negative",
        "傷": "negative",
        "傷感": "negative",
    }
    return alias_map.get(label, "neutral")


def _split_poem_segments(text):
    """Split poem text into reading segments."""
    raw_lines = [line.strip() for line in re.split(r'[\r\n]+', text) if line.strip()]
    if len(raw_lines) > 1:
        return raw_lines

    sentences = [segment.strip() for segment in re.split(r'(?<=[。！？!?；;])\s*', text) if segment.strip()]
    return sentences or [text.strip()]


def _build_sentence_items(text, emotion=None, sentence_emotions=None):
    """Build sentence items with per-sentence sentiment."""
    if sentence_emotions and isinstance(sentence_emotions, list):
        # 優先採用前端傳來的 Azure 逐句情緒，只用順序，不重新計算情緒文本。
        sentiments = []
        for item in sentence_emotions:
            if isinstance(item, dict):
                sentiments.append(_normalize_sentiment(item.get("sentiment") or item.get("emotion")))
            else:
                sentiments.append(_normalize_sentiment(item))

        segments = _split_poem_segments(text)
        if not segments:
            segments = [text.strip()]

        if sentiments and segments:
            fallback_sentiment = sentiments[-1]
            items = []
            for idx, segment in enumerate(segments):
                sentiment = sentiments[idx] if idx < len(sentiments) else fallback_sentiment
                items.append({
                    "text": segment,
                    "sentiment": sentiment,
                })
            return items

    # 若前端沒有傳逐句結果，才退回到本機切句 + 整體情緒。
    try:
        analyzer = EmotionAnalyzer()
        analysis = analyzer.analyze_emotion_with_details(text, language="zh-Hans")
        if analysis and analysis.get("sentences"):
            items = []
            for sentence in analysis["sentences"]:
                sentence_text = str(sentence.get("text") or "").strip()
                if not sentence_text:
                    continue
                items.append({
                    "text": sentence_text,
                    "sentiment": _normalize_sentiment(sentence.get("sentiment")),
                })
            if items:
                return items
    except Exception:
        pass

    fallback_sentiment = _normalize_sentiment(emotion)
    return [
        {
            "text": segment,
            "sentiment": fallback_sentiment,
        }
        for segment in _split_poem_segments(text)
        if segment
    ]


def _build_sentence_ssml(sentence_items, voice_name, rate_str, pitch_str):
    """Build SSML that changes style per sentence."""
    if not sentence_items:
        raise ValueError("沒有可朗讀的句子")

    chunks = []
    for item in sentence_items:
        sentence_text = xml_escape(item["text"])
        sentiment = _normalize_sentiment(item.get("sentiment"))
        azure_style = SENTIMENT_STYLE_MAP.get(sentiment, "general")
        chunks.append(
            f"""
            <mstts:express-as style="{azure_style}" styledegree="2">
                <prosody rate="{rate_str}" pitch="{pitch_str}">
                    {sentence_text}
                </prosody>
            </mstts:express-as>
            """
        )

    sentence_block = "<break time=\"220ms\"/>".join(chunks)
    return f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
        <voice name="{voice_name}">
            {sentence_block}
        </voice>
    </speak>
    """

def float_to_percent_str(value):
    """將浮點數轉換為 SSML 支援的百分比格式 (例如 1.5 -> '+50%', 0.8 -> '-20%')"""
    percent = int((value - 1.0) * 100)
    return f"+{percent}%" if percent >= 0 else f"{percent}%"

def generate_emotional_speech(text, emotion, speed=1.0, pitch=1.0, sentence_emotions=None):
    """
    Generate speech with per-sentence emotional styling when possible.
    """
    if not SPEECH_KEY or not SPEECH_REGION:
        raise ValueError("缺少 Azure Speech 的設定參數 (SPEECH_KEY 或 SPEECH_REGION)")

    # 1. 初始化 Azure Speech 
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz64KBitRateMonoMp3
    )
    
    # 使用老師範例中的聲音
    voice_name = "zh-CN-XiaoxiaoNeural"
    speech_config.speech_synthesis_voice_name = voice_name

    # 2. 準備存檔路徑 (使用時間戳確保檔名不重複)
    os.makedirs(os.path.join("static", "audio"), exist_ok=True)
    file_name = f"output_{int(time.time())}.mp3"
    relative_path = f"/static/audio/{file_name}"
    absolute_path = os.path.join("static", "audio", file_name)
    
    file_config = speechsdk.audio.AudioOutputConfig(filename=absolute_path)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, 
        audio_config=file_config
    )

    # 3. 處理語速與音調轉換
    rate_str = float_to_percent_str(speed)
    pitch_str = float_to_percent_str(pitch)

    # 4. Build per-sentence SSML so each line can sound different.
    sentence_items = _build_sentence_items(text, emotion=emotion, sentence_emotions=sentence_emotions)
    ssml_input = _build_sentence_ssml(sentence_items, voice_name, rate_str, pitch_str)

    # 5. 執行合成
    result = speech_synthesizer.speak_ssml_async(ssml_input).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # 取得音訊長度 (總秒數)
        duration_seconds = 0.0
        if result.audio_duration:
            duration_seconds = result.audio_duration.total_seconds()
            
        return {
            "audio_url": relative_path,
            "duration": round(duration_seconds, 2)
        }
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        error_msg = f"語音合成取消: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            error_msg += f", 詳細錯誤: {cancellation_details.error_details}"
        raise RuntimeError(error_msg)
