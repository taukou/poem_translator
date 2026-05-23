// DOM 元素
const inputText = document.getElementById('inputText');
const translateBtn = document.getElementById('translateBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const outputSection = document.getElementById('outputSection');
const modernText = document.getElementById('modernText');
const targetLang = document.getElementById('targetLang');
const outputText = document.getElementById('outputText');
const targetSelect = document.getElementById('targetSelect');
const poemSelect = document.getElementById('poemSelect');
const errorMessage = document.getElementById('errorMessage');
const spinner = document.getElementById('loadingSpinner');
const emotionSummary = document.getElementById('emotionSummary');
const emotionSentences = document.getElementById('emotionSentences');

let poemCatalog = [];

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
    } catch (error) {
        showError(error.message || '發生錯誤，請重試');
    } finally {
        showLoading(false);
    }
}

// 清除函數
function clearText() {
    inputText.value = '';
    if (poemSelect) {
        poemSelect.value = '';
    }
    modernText.textContent = '輸入古文後，這裡會顯示白話文解釋。';
    targetLang.textContent = '';
    outputText.textContent = '翻譯完成後，這裡會顯示目標語言的翻譯結果。';
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

    modernText.textContent = translation.modern_chinese || '';
    targetLang.textContent = translation.target_language || '';
    outputText.textContent = translation.translated || '';
    renderEmotionAnalysis(emotionAnalysis);
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 顯示錯誤訊息
function showError(message) {
    errorMessage.textContent = message;
    setHidden(errorMessage, false);
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

    fetch('/api/health')
        .then(response => {
            if (!response.ok) {
                showError('服務連接失敗，請稍後重試');
            }
        })
        .catch(() => {
            showError('無法連接到服務器');
        });

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
