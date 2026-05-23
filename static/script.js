// DOM 元素
const inputText = document.getElementById('inputText');
const translateBtn = document.getElementById('translateBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const outputSection = document.getElementById('outputSection');
const originalPoem = document.getElementById('originalPoem');
const modernText = document.getElementById('modernText');
const targetLang = document.getElementById('targetLang');
const outputText = document.getElementById('outputText');
const targetSelect = document.getElementById('targetSelect');
const poemSelect = document.getElementById('poemSelect');
const errorMessage = document.getElementById('errorMessage');
const spinner = document.getElementById('loadingSpinner');
const emotionSummary = document.getElementById('emotionSummary');
const emotionSentences = document.getElementById('emotionSentences');
const playBtn = document.getElementById('playBtn');
const emotionSelect = document.getElementById('emotionSelect');
const audioPlayer = document.getElementById('audioPlayer');
const contentExplanation = document.getElementById('contentExplanation');
const authorIntro = document.getElementById('authorIntro');
let poemCatalog = [];
let currentWordAnnotations = [];
let currentOriginalText = '';
let tooltipHideTimer = null;
let currentDetectedEmotion = '平'; // 用來記錄目前這首詩被分析出的情緒，預設為平靜

function setHidden(element, shouldHide) {
    if (!element) {
        return;
    }

    element.classList.toggle('hidden', shouldHide);
}

function formatScore(value) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return '0%';
    }

    return `${Math.round(value * 100)}%`;
}

function sentimentLabel(sentiment) {
    const mapping = {
        positive: '正向',
        neutral: '中性',
        negative: '負向'
    };

    return mapping[sentiment] || sentiment || '未知';
}

function formatPoemLabel(poem) {
    if (!poem) {
        return '';
    }

    const author = poem.author ? `｜${poem.author}` : '';
    const style = poem.style ? `｜${poem.style}` : '';
    return `${poem.title || '未命名'}${author}${style}`;
}

function fillPoemText(poemId) {
    const poem = poemCatalog.find((item) => String(item.id) === String(poemId));

    if (!poem) {
        return;
    }

    inputText.value = poem.text || '';
    hideError();
}

function escapeHTML(value) {
    return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function escapeRegExp(value) {
    return String(value || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function findAnnotation(word) {
    return currentWordAnnotations.find((annotation) => String(annotation.word || '') === String(word || ''));
}

function renderAnnotatedLine(line) {
    const annotations = [...currentWordAnnotations]
        .map((annotation) => String(annotation.word || '').trim())
        .filter(Boolean)
        .sort((a, b) => b.length - a.length);

    if (!annotations.length) {
        return escapeHTML(line);
    }

    let html = escapeHTML(line);
    const markers = [];

    annotations.forEach((word, index) => {
        const marker = `__POEM_WORD_${index}__`;
        const regex = new RegExp(escapeRegExp(word), 'g');
        if (regex.test(html)) {
            html = html.replace(regex, marker);
            markers.push({ marker, word });
        }
    });

    markers.forEach(({ marker, word }) => {
        html = html.replaceAll(
            marker,
            `<span class="poem-word" data-word="${escapeHTML(word)}">${escapeHTML(word)}</span>`
        );
    });

    return html;
}

function renderOriginalPoem(text) {
    if (!originalPoem) {
        return;
    }

    const existingTooltip = document.querySelector('.word-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
    if (tooltipHideTimer) {
        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = null;
    }

    const sourceText = String(text || '').trim();

    if (!sourceText) {
        originalPoem.classList.add('placeholder-text');
        originalPoem.textContent = '翻譯後，這裡會顯示原文。把滑鼠移到詞語上，就能看到 AI 註釋。';
        return;
    }

    const lines = sourceText.split(/\r?\n/).filter(Boolean);
    const html = lines.length
        ? lines.map((line) => `<div class="poem-line">${renderAnnotatedLine(line)}</div>`).join('')
        : `<div class="poem-line">${renderAnnotatedLine(sourceText)}</div>`;

    originalPoem.classList.remove('placeholder-text');
    originalPoem.innerHTML = html;
    setupPoemHover();
}

function setupPoemHover() {
    if (!originalPoem) {
        return;
    }

    originalPoem.querySelectorAll('.poem-word').forEach((wordEl) => {
        wordEl.addEventListener('mouseenter', showWordTooltip);
        wordEl.addEventListener('mouseleave', hideWordTooltipSoon);
    });
}

function showWordTooltip(event) {
    const wordEl = event.currentTarget;
    const word = wordEl.getAttribute('data-word');
    const annotation = findAnnotation(word);

    if (!annotation) {
        return;
    }

    if (tooltipHideTimer) {
        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = null;
    }

    let tooltip = document.querySelector('.word-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'word-tooltip';
        document.body.appendChild(tooltip);
    }

    tooltip.innerHTML = `
        <div class="tooltip-word">${escapeHTML(annotation.word || word)}</div>
        <div class="annotation-meaning">
            <span class="label">釋義：</span>
            <span>${escapeHTML(annotation.meaning || '無')}</span>
        </div>
        ${annotation.usage ? `
        <div class="annotation-usage">
            <span class="label">用法：</span>
            <span>${escapeHTML(annotation.usage)}</span>
        </div>
        ` : ''}
    `;

    const rect = wordEl.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    let left = rect.right + 12;
    let top = rect.top - (tooltipRect.height - rect.height) / 2;

    if (left + tooltipRect.width > window.innerWidth) {
        left = rect.left - tooltipRect.width - 12;
    }
    if (left < 12) {
        left = 12;
    }
    if (top < 12) {
        top = 12;
    } else if (top + tooltipRect.height > window.innerHeight - 12) {
        top = window.innerHeight - tooltipRect.height - 12;
    }

    tooltip.style.position = 'fixed';
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
    tooltip.style.zIndex = '10000';
    tooltip.dataset.visible = '1';
}

function hideWordTooltipSoon() {
    if (tooltipHideTimer) {
        clearTimeout(tooltipHideTimer);
    }

    tooltipHideTimer = setTimeout(() => {
        const tooltip = document.querySelector('.word-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
        tooltipHideTimer = null;
    }, 120);
}

function renderEmotionAnalysis(data) {
    if (!emotionSummary || !emotionSentences) {
        return;
    }

    const result = data || {};
    const scores = result.overall_scores || {};
    const sentiment = result.overall_sentiment || 'neutral';

    emotionSummary.classList.remove('empty-state');
    emotionSummary.innerHTML = `
        <div><strong>整體情緒：</strong>${sentimentLabel(sentiment)}</div>
        <div class="emotion-score-row">
            <span>正面</span>
            <div class="emotion-score-bar"><div class="emotion-score-fill" style="width:${Math.round((scores.positive || 0) * 100)}%;background:#14b8a6;"></div></div>
            <span>${formatScore(scores.positive)}</span>
        </div>
        <div class="emotion-score-row">
            <span>中立</span>
            <div class="emotion-score-bar"><div class="emotion-score-fill" style="width:${Math.round((scores.neutral || 0) * 100)}%;background:#94a3b8;"></div></div>
            <span>${formatScore(scores.neutral)}</span>
        </div>
        <div class="emotion-score-row">
            <span>負面</span>
            <div class="emotion-score-bar"><div class="emotion-score-fill" style="width:${Math.round((scores.negative || 0) * 100)}%;background:#ef4444;"></div></div>
            <span>${formatScore(scores.negative)}</span>
        </div>
    `;

    const sentences = Array.isArray(result.sentences) ? result.sentences : [];

    if (!sentences.length) {
        emotionSentences.innerHTML = '<div class="emotion-sentence"><div class="emotion-sentence-text">沒有可顯示的逐句分析結果。</div></div>';
        return;
    }

    emotionSentences.innerHTML = sentences.map((sentence) => {
        const opinions = Array.isArray(sentence.opinions) && sentence.opinions.length
            ? sentence.opinions.map((opinion) => `${opinion.target || '意見'}：${sentimentLabel(opinion.sentiment)}`).join('，')
            : '無';

        return `
            <div class="emotion-sentence">
                <div class="emotion-sentence-header">
                    <span>第 ${sentence.index || 0} 句</span>
                    <span>${sentimentLabel(sentence.sentiment)}</span>
                </div>
                <div class="emotion-sentence-text">${sentence.text || ''}</div>
                <div class="emotion-sentence-meta">
                    <div>分數：正面 ${formatScore(sentence.scores && sentence.scores.positive)}, 中立 ${formatScore(sentence.scores && sentence.scores.neutral)}, 負面 ${formatScore(sentence.scores && sentence.scores.negative)}</div>
                    <div>意見：${opinions}</div>
                </div>
            </div>
        `;
    }).join('');
}

// 翻譯 + 情緒分析
async function translate() {
    const text = inputText.value.trim();

    if (!text) {
        showError('請輸入要翻譯的文本');
        return;
    }

    try {
        showLoading(true);
        hideError();

        const response = await fetch('/api/translate-and-analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                target_language: targetSelect ? targetSelect.value : 'de'
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '翻譯失敗，請重試');
        }

        const data = await response.json();
        displayResult(data);
        
        // 獲取 AI 詳細分析
        await fetchAIAnalysis(text);
    } catch (error) {
        showError(error.message || '發生錯誤，請重試');
    } finally {
        showLoading(false);
    }
}

// 獲取 AI 詳細分析
async function fetchAIAnalysis(text) {
    try {
        const response = await fetch('/api/translate-detailed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                target_language: 'zh-Hant'
            })
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            const message = data.error || `AI 註釋失敗（HTTP ${response.status}）`;
            showError(message);
            displayAIAnalysis({ error: message });
            return;
        }

        const data = await response.json();
        if (data.error) {
            showError(data.error);
        }
        displayAIAnalysis(data);
    } catch (error) {
        const message = `AI 註釋失敗：${error.message}`;
        showError(message);
        displayAIAnalysis({ error: message });
    }
}

// 清除函數
function clearText() {
    inputText.value = '';
    if (poemSelect) {
        poemSelect.value = '';
    }
    currentOriginalText = '';
    currentWordAnnotations = [];
    if (tooltipHideTimer) {
        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = null;
    }
    if (document.querySelector('.word-tooltip')) {
        document.querySelector('.word-tooltip').remove();
    }
    if (originalPoem) {
        originalPoem.textContent = '翻譯後，這裡會顯示原文。把滑鼠移到詞語上，就能看到 AI 註釋。';
        originalPoem.classList.add('placeholder-text');
    }
    modernText.textContent = '輸入古文後，這裡會顯示白話文解釋。';
    modernText.classList.add('placeholder-text');
    targetLang.textContent = '';
    outputText.textContent = '翻譯完成後，這裡會顯示目標語言的翻譯結果。';
    outputText.classList.add('placeholder-text');
    
    contentExplanation.textContent = '進行翻譯後，這裡會顯示詩文的詳細解釋。';
    contentExplanation.classList.add('placeholder-text');
    authorIntro.textContent = '進行翻譯後，這裡會顯示作者的生平和介紹。';
    authorIntro.classList.add('placeholder-text');
    
    if (emotionSummary) {
        emotionSummary.classList.add('empty-state');
        emotionSummary.textContent = '等待分析結果。';
    }
    if (emotionSentences) {
        emotionSentences.innerHTML = '';
    }
    hideError();
    inputText.focus();
}

// 複製函數
function copyText() {
    if (outputText.textContent) {
        navigator.clipboard.writeText(outputText.textContent)
            .then(() => {
                showSuccess('已複製翻譯結果');
            })
            .catch(() => {
                showError('複製失敗，請重試');
            });
    }
}

// 顯示結果
function displayResult(data) {
    const translation = data.translation || data;
    const emotionAnalysis = data.emotion_analysis || {};
    currentOriginalText = translation.original || inputText.value || '';
    currentWordAnnotations = [];

    renderOriginalPoem(currentOriginalText);
    modernText.textContent = translation.modern_chinese || '';
    targetLang.textContent = translation.target_language || '';
    outputText.textContent = translation.translated || '';
    renderEmotionAnalysis(emotionAnalysis);
    
    // 自動轉換並記錄情緒變數
    if (emotionAnalysis.overall_sentiment) {
        const sentiment = emotionAnalysis.overall_sentiment;
        if (sentiment === "positive") {
            currentDetectedEmotion = "喜";
        } else if (sentiment === "negative") {
            currentDetectedEmotion = "悲";
        } else {
            currentDetectedEmotion = "平"; // neutral 或 mixed 都回歸平靜
        }
    }

    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 顯示 AI 詳細分析
function displayAIAnalysis(data) {
    if (!data || data.error) {
        if (contentExplanation) {
            contentExplanation.classList.add('placeholder-text');
            contentExplanation.textContent = '進行翻譯後，這裡會顯示詩文的詳細解釋。';
        }
        if (authorIntro) {
            authorIntro.classList.add('placeholder-text');
            authorIntro.textContent = '進行翻譯後，這裡會顯示作者的生平和介紹。';
        }
        return;
    }

    if (!data.analysis) {
        return;
    }

    const analysis = data.analysis || {};
    
    // 顯示內容解釋
    if (analysis.content_explanation) {
        const contentExpl = analysis.content_explanation;
        let contentHTML = `
            <div class="content-explanation">
                <div class="explanation-section">
                    <h4>整體含義</h4>
                    <p>${contentExpl.overall_meaning || ''}</p>
                </div>
                <div class="explanation-section">
                    <h4>核心主旨</h4>
                    <p>${contentExpl.central_theme || ''}</p>
                </div>
                <div class="explanation-section">
                    <h4>意境</h4>
                    <p>${contentExpl.artistic_conception || ''}</p>
                </div>
                ${contentExpl.line_by_line_analysis && contentExpl.line_by_line_analysis.length ? `
                <div class="explanation-section">
                    <h4>逐句分析</h4>
                    <ul class="line-analysis">
                        ${contentExpl.line_by_line_analysis.map((line, idx) => `<li><strong>第 ${idx + 1} 句：</strong> ${line}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        `;
        contentExplanation.innerHTML = contentHTML;
        contentExplanation.classList.remove('placeholder-text');
    }
    
    if (analysis.word_annotations && Array.isArray(analysis.word_annotations)) {
        currentWordAnnotations = analysis.word_annotations;
        renderOriginalPoem(currentOriginalText);
    }
    
    // 顯示作者介紹
    if (analysis.author_introduction) {
        const author = analysis.author_introduction;
        let authorHTML = `
            <div class="author-intro">
                ${author.name ? `<div class="author-name"><strong>作者：</strong> ${author.name}</div>` : ''}
                ${author.period ? `<div class="author-period"><strong>時代：</strong> ${author.period}</div>` : ''}
                ${author.biography ? `<div class="author-biography"><strong>生平：</strong> ${author.biography}</div>` : ''}
                ${author.literary_style ? `<div class="author-style"><strong>文學風格：</strong> ${author.literary_style}</div>` : ''}
                ${author.achievements ? `<div class="author-achievements"><strong>成就：</strong> ${author.achievements}</div>` : ''}
                ${author.poem_status ? `<div class="author-poem-status"><strong>本詩地位：</strong> ${author.poem_status}</div>` : ''}
            </div>
        `;
        authorIntro.innerHTML = authorHTML;
        authorIntro.classList.remove('placeholder-text');
    }
}

// 顯示錯誤訊息
function showError(message) {
    hideError();
    window.alert(message || '發生錯誤，請稍後再試');
}

// 隱藏錯誤訊息
function hideError() {
    setHidden(errorMessage, true);
    errorMessage.textContent = '';
}

// 顯示成功訊息
function showSuccess(message) {
    errorMessage.classList.remove('hidden');
    errorMessage.textContent = message;
    errorMessage.style.backgroundColor = 'rgba(20, 184, 166, 0.12)';
    errorMessage.style.color = '#0f766e';
    errorMessage.style.borderLeftColor = '#14b8a6';

    setTimeout(() => {
        hideError();
        errorMessage.style.backgroundColor = 'rgba(180, 35, 24, 0.08)';
        errorMessage.style.color = '#b42318';
        errorMessage.style.borderLeftColor = '#b42318';
    }, 2000);
}

// 顯示/隱藏載入動畫
function showLoading(isLoading) {
    setHidden(spinner, !isLoading);
    translateBtn.disabled = isLoading;
}

// 事件監聽器
translateBtn.addEventListener('click', translate);
clearBtn.addEventListener('click', clearText);
copyBtn.addEventListener('click', copyText);

if (poemSelect) {
    poemSelect.addEventListener('change', (event) => {
        fillPoemText(event.target.value);
    });
}

// 支持Enter快捷鍵
inputText.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        translate();
    }
});

// 語音播放功能
async function playSpeech() {
    const originalText = inputText.value.trim();
    // 直接讀取系統剛剛幫你存好的情緒變數
    const emotion = currentDetectedEmotion; 

    if (!originalText) {
        showError('沒有可播放的原始文本');
        return;
    }

    try {
        playBtn.disabled = true;
        playBtn.textContent = '合成語音中...';
        hideError();

        const speechRes = await fetch('/api/generate-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: originalText,
                emotion: emotion,
                speed: 1.0,
                pitch: 1.0
            })
        });

        if (!speechRes.ok) {
            const data = await speechRes.json();
            throw new Error(data.error || '語音合成失敗');
        }

        const speechData = await speechRes.json();
        
        audioPlayer.src = speechData.audio_url;
        audioPlayer.play();
        
        showSuccess(`已自動偵測情緒「${emotion}」，開始朗讀原文`);

    } catch (error) {
        showError(error.message || '發生錯誤，請重試');
    } finally {
        playBtn.disabled = false;
        playBtn.textContent = '朗讀原文';
    }
}

// 綁定按鈕事件（單次綁定）
if (playBtn) playBtn.addEventListener('click', playSpeech);

// 頁面加載時檢查服務狀態
document.addEventListener('DOMContentLoaded', () => {
    if (modernText && !modernText.textContent.trim()) {
        modernText.textContent = '輸入古文後，這裡會顯示白話文解釋。';
    }
    if (outputText && !outputText.textContent.trim()) {
        outputText.textContent = '翻譯完成後，這裡會顯示目標語言的翻譯結果。';
    }

    fetch('/api/poems')
        .then((response) => response.json())
        .then((data) => {
            poemCatalog = Array.isArray(data.poems) ? data.poems : [];

            if (!poemSelect) {
                return;
            }

            poemSelect.innerHTML = '<option value="">請選擇詩名</option>';

            poemCatalog.forEach((poem) => {
                const option = document.createElement('option');
                option.value = poem.id;
                option.textContent = formatPoemLabel(poem);
                poemSelect.appendChild(option);
            });
        })
        .catch(() => {
            if (poemSelect) {
                poemSelect.innerHTML = '<option value="">詩詞清單載入失敗</option>';
            }
        });

    // 設置 example 按鈕事件監聽器
    const example1 = document.getElementById('example1');
    const example2 = document.getElementById('example2');
    const example3 = document.getElementById('example3');

    if (example1) {
        example1.addEventListener('click', () => {
            inputText.value = '獨坐幽篁裡，彈琴復長嘯。深林人不知，明月來相照。';
        });
    }

    if (example2) {
        example2.addEventListener('click', () => {
            inputText.value = '國破山河在，城春草木深。感時花濺淚，恨別鳥驚心。烽火連三月，家書抵萬金。白頭搔更短，渾欲不勝簪。';
        });
    }

    if (example3) {
        example3.addEventListener('click', () => {
            inputText.value = '床前明月光，疑是地上霜。舉頭望明月，低頭思故鄉。';
        });
    }
});

