import os
import time
import configparser
import azure.cognitiveservices.speech as speechsdk

# 讀取 Config (這裡假設你是在專案根目錄執行)
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# 確保 config.ini 裡面有 [AzureSpeech] 區塊
SPEECH_KEY = config.get('AzureSpeech', 'SPEECH_KEY', fallback='')
SPEECH_REGION = config.get('AzureSpeech', 'SPEECH_REGION', fallback='')

def float_to_percent_str(value):
    """將浮點數轉換為 SSML 支援的百分比格式 (例如 1.5 -> '+50%', 0.8 -> '-20%')"""
    percent = int((value - 1.0) * 100)
    return f"+{percent}%" if percent >= 0 else f"{percent}%"

def generate_emotional_speech(text, emotion, speed=1.0, pitch=1.0):
    """
    根據給定的情緒、語速和音調生成語音
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

    # 3. 處理情緒對應 (Azure XiaoxiaoNeural 支援的 style)
    style_map = {
        "喜": "cheerful",
        "悲": "sad",
        "怒": "angry",
        "懼": "terrified",
        "平": "general"
    }
    azure_style = style_map.get(emotion, "general")

    # 4. 處理語速與音調轉換
    rate_str = float_to_percent_str(speed)
    pitch_str = float_to_percent_str(pitch)

    # 5. 組合 SSML
    # 注意：如果 azure_style 是 general，其實不需要 express-as 標籤，但包含進去設為 general 也是被允許的。
    ssml_input = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
        <voice name="{voice_name}">
            <mstts:express-as style="{azure_style}" styledegree="2">
                <prosody rate="{rate_str}" pitch="{pitch_str}">
                    {text}
                </prosody>
            </mstts:express-as>
        </voice>
    </speak>
    """

    # 6. 執行合成
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