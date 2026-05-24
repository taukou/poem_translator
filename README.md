# 詩詞翻譯與情感語音合成系統 (Poem Translator with Emotional TTS)

NLP期末專項 - 一個基於Flask框架的古詩詞翻譯應用，集成情緒分析和動態語音合成。

## 📋 功能特性

- 🎨 現代化的用戶界面，支持實時可視化
- ⚡ 快速的翻譯響應（Azure Translator API）
- 😊 逐字情緒分析與標記（多維度情感標籤）
- 🎤 情感語音合成（根據情緒動態調整音調、語速）
- 📊 情緒分布可視化展示
- 📱 響應式設計，支持移動設備
- 🔒 安全的密鑰管理
- 🚀 基於Flask的輕量級後端
- 🎯 支持批量詩詞分析

## 📁 項目結構

```
poem_translator/
├── app.py                 # Flask應用主文件
├── config.ini            # 配置範本
├── requirements.txt      # Python依賴
├── .gitignore           # Git忽略文件
├── .env.example         # 環境變量示例
├── README.md            # 項目文檔
├── utils/               # 工具模塊
│   ├── __init__.py      # 包初始化文件
│   ├── translator.py    # 翻譯模塊
│   ├── emotion_analyzer.py    # 情緒分析模塊
│   ├── text_processor.py      # 文本處理與分詞
│   └── tts_engine.py          # 文本轉語音引擎
├── templates/           # HTML模板
│   └── index.html       # 主頁面
└── static/              # 靜態資源
    ├── style.css        # 樣式表
    └── script.js        # 前端邏輯
```

## 🛠️ 安裝步驟

### 1. 創建虛擬環境（建議）

```bash
python -m venv venv
```

#### Windows激活虛擬環境：
```bash
venv\Scripts\activate
```

#### macOS/Linux激活虛擬環境：
```bash
source venv/bin/activate
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 配置密鑰

編輯 `config.ini`：

```ini

[AzureTranslator]
Key = your key
Region = your region
Endpoint = your endpoint
[AZURELANGUAGE]
AZURE_LANGUAGE_KEY = your key
AZURE_LANGUAGE_ENDPOINT = your endpoint
```

## 🚀 運行應用

```bash
python app.py
```

應用將在 `http://localhost:5000` 上運行

## 📖 使用說明

1. 打開瀏覽器訪問 `http://localhost:5000`
2. 在輸入框輸入要翻譯的古詩詞
3. 點擊「翻譯」按鈕或使用快捷鍵 `Ctrl+Enter`
4. 翻譯結果將顯示在下方
5. 點擊「複製結果」將翻譯內容複製到剪貼板

## 🔌 API 端點

### `/` (GET)
主頁面，返回HTML

### `/api/translate` (POST)
翻譯端點

**請求：**
```json
{
  "text": "要翻譯的古文"
}
```

**響應：**
```json
{
  "original": "原始文本",
  "translated": "翻譯結果"
}
```

### `/api/analyze-emotion` (POST)
情緒分析端點 - 逐字分析情緒

**請求：**
```json
{
  "text": "要分析的文本"
}
```

**響應：**
```json
{
  "emotions": [
    {"char": "字", "emotion": "喜", "score": 0.85},
    {"char": "詞", "emotion": "悲", "score": 0.92}
  ],
  "overall_emotion": "悲"
}
```

### `/api/generate-speech` (POST)
情感語音合成端點 - 根據情緒調整音調和語速

**請求：**
```json
{
  "text": "要轉換的文本",
  "emotion": "喜|悲|怒|懼|平",
  "speed": 1.0,
  "pitch": 1.0
}
```

**響應：**
```json
{
  "audio_url": "/static/audio/output.mp3",
  "duration": 5.2
}
```

### `/api/health` (GET)
健康檢查端點


⚠️ **重要**：
- 不要將 `config.ini` 提交到版本控制系統
- `.gitignore` 已配置為忽略此文件
- 在生產環境中使用環境變量代替密鑰
- 定期更新依賴包

## 📦 依賴包

- Flask 3.0.0 - Web框架
- flask-cors 4.0.0 - 跨域資源共享
- configparser 6.0.0 - 配置文件解析
- nltk - 自然語言處理
- jieba - 中文分詞
- snownlp - 中文情感分析
- azure-cognitiveservices-language-textanalytics - Azure文本分析
- pyttsx3 - 文本轉語音
- requests - HTTP請求庫

此外，專案中也使用了新版 Azure SDK 套件（請確保在 `requirements.txt` 中列出）：

- azure-ai-textanalytics - Azure Text Analytics（推薦使用，為新版 SDK，通常取代 `azure-cognitiveservices-language-textanalytics`）
- azure-ai-translation-text - Azure 翻譯服務（Translator）
- azure-core - Azure 共用核心庫（新版 Azure SDK 依賴）

說明：如果你同時看到 `azure-cognitiveservices-language-textanalytics` 與 `azure-ai-textanalytics`，請注意前者為舊版套件，建議以 `azure-ai-textanalytics` 為主，或在 README 中註明替代關係。

## 🔧 新增 API 與前端變更

- **新 API：** `/api/translate-and-analyze` — 一次回傳翻譯與情緒分析結果（JSON），方便前端一次請求取得全部顯示內容。
- **新 API：** `/api/poems` 與 `/api/poems/<id>` — 提供唐詩清單與單首詩的內容，供前端下拉選擇使用。
- **前端變更：** UI 改為雙欄（輸入在左、結果在右）；右側預設三張卡片顯示「白話文」「翻譯」「情緒分析」；新增下拉選單 `poemSelect`，可從 `唐詩三百首.txt` 選擇詩名並自動填入輸入區。
- **注意事項：** README 先前範例使用的 config section 名稱（如 `[AZURE]` 或 `[API]`）與程式實際讀取的 `[AzureTranslator]` / `[AZURELANGUAGE]` 可能不一致，請統一或在文件中標註對應關係以避免初始化失敗錯誤。

## 💡 核心功能規劃

### Phase 1: 基礎翻譯與情緒分析（MVP）
- [x] 古文翻譯模塊
- [ ] 逐字情緒判斷
- [ ] 情緒可視化標記（顏色編碼）
- [ ] 基礎TTS功能

### Phase 2: 情感語音合成
- [ ] 情緒-音調對應關係
- [ ] 語速動態調整
- [ ] 音量與停頓控制
- [ ] 播放控制（暫停、快進、調速）

### Phase 3: 數據展示與分析
- [ ] 情緒分布圖表（柱狀圖/圓餅圖）
- [ ] 並排展示原文+翻譯+情緒標記
- [ ] 情緒轉折點分析
- [ ] 詩詞情緒傾向評分

### Phase 4: 高級特性
- [ ] 聲音特效（回音、混音）
- [ ] 批量詩詞分析
- [ ] 分析結果導出
- [ ] 歷史記錄保存
- [ ] 用戶反饋機制

## 🐛 故障排除

### 無法連接到服務器
- 檢查Flask服務是否正在運行
- 確認端口 5000 未被其他應用占用

### 翻譯失敗
- 檢查 `config.ini` 中的密鑰是否正確設置
- 確保API服務可正常訪問

### 模板找不到錯誤
- 確保 `templates` 和 `static` 目錄在正確位置
- 檢查文件名是否正確
