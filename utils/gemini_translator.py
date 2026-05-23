"""
utils/gemini_translator.py

功能說明：
    本模組負責使用 Google Gemini API 進行古詩詞的深入解釋和分析。

主要功能：
    1. 詳細解釋古詩的內容、意境和主旨
    2. 詞語註釋 - 解釋文言文中的關鍵詞彙
    3. 作者介紹 - 介紹詩歌作者的生平和文學成就

主要提供給後端 API 對接的函式：
    translate_and_analyze(text, target_language="zh-Hant")
    analyze_poem_emotions(text)
    compare_poems(text1, text2)

使用範例：
    from utils.gemini_translator import translate_and_analyze

    result = translate_and_analyze("昔日戲言身後事，今朝都到眼前來。")
    print(result)

回傳格式：
    {
        "original": "原始文言文",
        "modern_chinese": "白話中文",
        "target_language": "zh-Hant",
        "analysis": {
            "content_explanation": {
                "overall_meaning": "整體含義",
                "line_by_line_analysis": ["第一句解釋", "第二句解釋", ...],
                "central_theme": "核心主旨",
                "artistic_conception": "意境描述"
            },
            "word_annotations": [
                {
                    "word": "詞彙",
                    "meaning": "含義",
                    "usage": "用法說明"
                }
            ],
            "author_introduction": {
                "name": "作者名字",
                "period": "時代",
                "biography": "生平簡介",
                "literary_style": "文學風格",
                "achievements": "主要成就",
                "poem_status": "該詩在其作品中的地位"
            }
        }
    }

注意事項：
    1. 需要在 config.ini 中配置 GEMINI.gemini_api_key
    2. requirements.txt 需要安裝 google-generativeai
    3. 需要有 utils.translator 模組支持
"""

import configparser
import json
import re
import os
import requests
from utils.translator import classical_to_modern_chinese, azure_translate

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_config():
    """获取配置对象，使用正确的文件路径"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
    config.read(config_path, encoding="utf-8")
    return config


def _extract_gemini_text(response_data: dict) -> str:
    """Extract the first text part from a Gemini response."""
    candidates = response_data.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini API returned no candidates: {response_data}")

    content = candidates[0].get("content", {})
    parts = content.get("parts") or []
    if not parts:
        return ""

    return parts[0].get("text", "")


def _call_gemini(prompt: str, gemini_api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> str:
    """Call Gemini with JSON output enabled."""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gemini_api_key,
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return _extract_gemini_text(response.json())


def _parse_json_response(response_text: str, fallback: dict) -> dict:
    """Parse Gemini JSON output, with a fallback for slightly noisy responses."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

    return fallback


def translate_and_analyze(text: str, target_language: str = "zh-Hant") -> dict:
    """
    使用 Google Gemini API REST 進行詳細解釋、詞語註釋和作者介紹
    
    Args:
        text: 要解釋的古文/詩文
        target_language: 目標語言代碼 (預設 zh-Hant)
    
    Returns:
        包含詳細解釋、詞語註釋和作者介紹的字典
    """
    try:
        # 獲取 Gemini API 密鑰
        config = get_config()
        gemini_api_key = config.get("GEMINI", "gemini_api_key", fallback=None)
        if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
            return {
                "error": "Gemini API 密鑰未配置。請在 config.ini 中設置 GEMINI.gemini_api_key",
                "original": text
            }
        
        # 先用 Azure 翻譯成現代中文
        modern_chinese = classical_to_modern_chinese(text)
        
        # 構建詳細解釋提示
        prompt = f"""請對以下古詩進行深入分析和解釋，使用 JSON 格式回覆：

【原文】
{text}

【白話翻譯】
{modern_chinese}

請提供以下內容（必須是有效的 JSON）：
{{
    "content_explanation": {{
        "overall_meaning": "整體含義",
        "line_by_line_analysis": ["第一句解釋", "第二句解釋"],
        "central_theme": "核心主旨",
        "artistic_conception": "意境描述"
    }},
    "word_annotations": [
        {{
            "word": "詞彙",
            "meaning": "含義",
            "usage": "用法說明"
        }}
    ],
    "author_introduction": {{
        "name": "作者名字",
        "period": "時代",
        "biography": "生平簡介",
        "literary_style": "文學風格",
        "achievements": "主要成就",
        "poem_status": "該詩在其作品中的地位"
    }}
}}"""

        response_text = _call_gemini(prompt, gemini_api_key)
        fallback_analysis = {
            "content_explanation": {
                "overall_meaning": response_text,
                "line_by_line_analysis": [],
                "central_theme": "",
                "artistic_conception": ""
            },
            "word_annotations": [],
            "author_introduction": {
                "name": "",
                "period": "",
                "biography": "",
                "literary_style": "",
                "achievements": "",
                "poem_status": ""
            }
        }
        analysis = _parse_json_response(response_text, fallback_analysis)
        
        return {
            "original": text,
            "modern_chinese": modern_chinese,
            "target_language": target_language,
            "analysis": analysis
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Gemini API 詳細解釋失敗: {str(e)}",
            "original": text
        }
    except Exception as e:
        return {
            "error": f"Gemini API 詳細解釋失敗: {str(e)}",
            "original": text
        }


def analyze_poem_emotions(text: str) -> dict:
    """
    使用 Gemini API 分析古詩的情感特徵
    
    Args:
        text: 要分析的古文/詩文
    
    Returns:
        包含情感分析的字典
    """
    try:
        config = get_config()
        gemini_api_key = config.get("GEMINI", "gemini_api_key", fallback=None)
        if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
            return {
                "error": "Gemini API 密鑰未配置。請在 config.ini 中設置 GEMINI.gemini_api_key"
            }
        
        prompt = f"""請分析以下古詩的情感特徵，使用 JSON 格式回覆：

【古詩】
{text}

回覆格式（必須是有效的 JSON）：
{{
    "primary_emotion": "...",
    "emotion_intensity": 0,
    "emotion_words": ["...", "...", "..."],
    "tone": "...",
    "mood": "...",
    "emotional_journey": "..."
}}"""

        response_text = _call_gemini(prompt, gemini_api_key)
        emotion_analysis = _parse_json_response(response_text, {
            "error": "無法解析情感分析結果",
            "raw_response": response_text
        })
        
        return emotion_analysis
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Gemini API 情感分析失敗: {str(e)}"
        }
    except Exception as e:
        return {
            "error": f"Gemini API 情感分析失敗: {str(e)}"
        }


def compare_poems(text1: str, text2: str) -> dict:
    """
    使用 Gemini API 比較兩首詩的風格和特點
    
    Args:
        text1: 第一首古詩
        text2: 第二首古詩
    
    Returns:
        包含比較結果的字典
    """
    try:
        config = get_config()
        gemini_api_key = config.get("GEMINI", "gemini_api_key", fallback=None)
        if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
            return {
                "error": "Gemini API 密鑰未配置。請在 config.ini 中設置 GEMINI.gemini_api_key"
            }
        
        prompt = f"""請比較以下兩首古詩，使用 JSON 格式回覆：

【古詩1】
{text1}

【古詩2】
{text2}

回覆格式（必須是有效的 JSON）：
{{
    "similarities": ["...", "..."],
    "differences": ["...", "..."],
    "style_comparison": "...",
    "theme_comparison": "...",
    "emotion_comparison": "...",
    "literary_techniques": "..."
}}"""

        response_text = _call_gemini(prompt, gemini_api_key)
        comparison = _parse_json_response(response_text, {
            "error": "無法解析比較結果",
            "raw_response": response_text
        })
        
        return {
            "poem1": text1,
            "poem2": text2,
            "comparison": comparison
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Gemini API 詩歌比較失敗: {str(e)}"
        }
    except Exception as e:
        return {
            "error": f"Gemini API 詩歌比較失敗: {str(e)}"
        }
