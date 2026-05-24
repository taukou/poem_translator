# 詩詞翻譯與情感語音合成系統

## 主要功能

- 古文 -> 現代中文（使用 Azure Translator）
- 進一步解釋 / 詞語註釋（可選：使用 Google Gemini API）
- 情緒分析（使用 Azure Text Analytics）
- 情感語音合成（使用 Azure Speech SDK，支援逐句不同情緒風格）
- 提供詩詞列表接口，支援從 `唐詩三百首.txt` 載入

## 專案結構（與程式碼一致）

```
poem_translator/
├── app.py                     # Flask 應用與 API 路由
├── config.ini                 # 服務金鑰與端點設定
├── requirements.txt           # Python 依賴
├── README.md                  # 專案說明（本檔）
├── 唐詩三百首.txt             # 詩詞資料來源
├── templates/                 # HTML 模板
│   └── index.html
├── static/                    # 靜態資源（包含產出的 audio 目錄）
│   ├── audio/
│   ├── script.js
│   └── style.css
└── utils/                     # 工具模組
    ├── __init__.py
    ├── translator.py         # Azure 翻譯包裝器（文言 -> 白話 -> 目標語言）
    ├── gemini_translator.py  # 使用 Google Gemini 做深入解釋 / 分析
    ├── emotion_analyzer.py   # Azure Text Analytics 情緒分析封裝
    └── speech_generator.py   # Azure Speech TTS（支援逐句情緒風格）
```

## 安裝與執行

1. 建議建立虛擬環境：

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

2. 安裝依賴：

```bash
pip install -r requirements.txt
```

3. 建立並編輯 `config.ini`（範例欄位）

```
[AzureTranslator]
Key = your_translator_key
Region = your_region
Endpoint = https://api.cognitive.microsofttranslator.com/

[AZURELANGUAGE]
AZURE_LANGUAGE_KEY = your_text_analytics_key
AZURE_LANGUAGE_ENDPOINT = https://<your-text-analytics-endpoint>

[AzureSpeech]
SPEECH_KEY = your_speech_key
SPEECH_REGION = your_speech_region

[GEMINI]
gemini_api_key = your_gemini_api_key  
```


4. 啟動應用：

```bash
python app.py
```

應用預設在 http://localhost:5000

## 已實作的 API（重點）

- `GET /api/poems` — 回傳從 `唐詩三百首.txt` 讀取的詩詞清單
- `GET /api/poems/<id>` — 取得單首詩的內容
- `POST /api/translate` — 翻譯古文（文言 -> 白話 -> 目標語言）
  - 請求: `{ "text": "...", "target_language": "zh-Hant" }`
  - 回傳: `{ "original": ..., "modern_chinese": ..., "translated": ... }`

- `POST /api/translate-detailed` — 使用 Gemini（若配置）做深入解析（含詞語註釋、作者介紹）
  - 請求: `{ "text": "...", "target_language": "zh-Hant" }`
  - 回傳: 視 Gemini 回應結構而定；若未配置 GEMINI key，會回傳包含 `error` 的物件

- `POST /api/analyze-poem-emotions` — 使用 Gemini 做詩歌情感特徵分析（若配置）

- `POST /api/analyze-emotion` — 使用 Azure Text Analytics 進行情緒與逐句分析
  - 請求: `{ "text": "..." }`
  - 回傳: 包含 `overall_sentiment`, `overall_scores`, `sentences` 等詳細欄位

- `POST /api/translate-and-analyze` — 先翻譯再對白話文本做情緒分析（一次回傳翻譯與情緒分析）

- `POST /api/generate-speech` — 使用 Azure Speech SDK 產生情感語音（存成 static/audio/*.mp3）
  - 請求範例: `{ "text": "...", "emotion": "平", "speed": 1.0, "pitch": 1.0, "sentence_emotions": [...] }`
  - 回傳: `{ "audio_url": "/static/audio/output_<ts>.mp3", "duration": 秒數 }

- `GET /api/health` — 健康檢查，回傳 `{ "status": "ok" }`

## 注意事項與實作差異

- 本專案內部使用的模組名稱與 README 早期範例已同步更新：實作檔案請見 `utils/`。
- `gemini_translator.py` 依賴 Google Gemini API，為選用功能；若未提供 GEMINI API key，相關路由會回傳錯誤訊息而非擲出例外。
- 主要情緒與語音功能以 Azure 服務為主：請在 `config.ini` 提供對應金鑰或以環境變數覆寫。

## 偵錯小技巧

- 若遇到情緒分析初始化錯誤，請檢查 `config.ini` 中 `[AZURELANGUAGE]` 的 key 與 endpoint 是否正確。
- 若語音合成失敗，確認 `[AzureSpeech]` 的 `SPEECH_KEY` 與 `SPEECH_REGION` 已設定，且本機可以連到 Azure 服務。

## 依賴（請以 `requirements.txt` 為準）

- Flask, flask-cors, azure-ai-textanalytics / azure-ai-translation-text, azure-cognitiveservices-speech, google-generativeai 等

---
