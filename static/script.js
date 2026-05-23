// DOM 元素
const inputText = document.getElementById('inputText');
const translateBtn = document.getElementById('translateBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const outputSection = document.getElementById('outputSection');
const outputText = document.getElementById('outputText');
const errorMessage = document.getElementById('errorMessage');
const spinner = document.getElementById('loadingSpinner');

// 翻譯函數
async function translate() {
    const text = inputText.value.trim();

    if (!text) {
        showError('請輸入要翻譯的文本');
        return;
    }

    try {
        showLoading(true);
        hideError();

        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '翻譯失敗，請重試');
        }

        const data = await response.json();
        displayResult(data.translated);

    } catch (error) {
        showError(error.message || '發生錯誤，請重試');
    } finally {
        showLoading(false);
    }
}

// 清除函數
function clearText() {
    inputText.value = '';
    outputText.textContent = '';
    outputSection.style.display = 'none';
    hideError();
    inputText.focus();
}

// 複製函數
function copyText() {
    if (outputText.textContent) {
        navigator.clipboard.writeText(outputText.textContent)
            .then(() => {
                showSuccess('已複製到剪貼板');
            })
            .catch(() => {
                showError('複製失敗，請重試');
            });
    }
}

// 顯示結果
function displayResult(result) {
    outputText.textContent = result;
    outputSection.style.display = 'block';
    outputText.scrollIntoView({ behavior: 'smooth' });
}

// 顯示錯誤訊息
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

// 隱藏錯誤訊息
function hideError() {
    errorMessage.style.display = 'none';
    errorMessage.textContent = '';
}

// 顯示成功訊息
function showSuccess(message) {
    errorMessage.style.display = 'block';
    errorMessage.textContent = message;
    errorMessage.style.backgroundColor = '#e8f5e9';
    errorMessage.style.color = '#2e7d32';
    errorMessage.style.borderLeftColor = '#2e7d32';

    setTimeout(() => {
        hideError();
        errorMessage.style.backgroundColor = '#ffebee';
        errorMessage.style.color = '#c62828';
        errorMessage.style.borderLeftColor = '#c62828';
    }, 2000);
}

// 顯示/隱藏載入動畫
function showLoading(isLoading) {
    if (isLoading) {
        spinner.classList.remove('hidden');
        translateBtn.disabled = true;
    } else {
        spinner.classList.add('hidden');
        translateBtn.disabled = false;
    }
}

// 事件監聽器
translateBtn.addEventListener('click', translate);
clearBtn.addEventListener('click', clearText);
copyBtn.addEventListener('click', copyText);

// 支持Enter快捷鍵
inputText.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        translate();
    }
});

// 頁面加載時檢查服務狀態
document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/health')
        .then(response => {
            if (!response.ok) {
                showError('服務連接失敗，請稍後重試');
            }
        })
        .catch(() => {
            showError('無法連接到服務器');
        });
});
