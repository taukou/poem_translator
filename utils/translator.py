"""
utils/translator.py

功能說明：
    本模組負責詩詞翻譯功能，使用 Azure Translator API。

翻譯流程：
    1. 將文言文 / 古詩 lzh 轉成白話繁體中文 zh-Hant
    2. 再將白話繁體中文 zh-Hant 翻譯成指定語言，例如德文 de

主要提供給後端 API 對接的函式：
    translate_poem(text, target_language="de")

使用範例：
    from utils.translator import translate_poem

    result = translate_poem("昔日戲言身後事，今朝都到眼前來。", "de")
    print(result)

回傳格式：
    {
        "original": "原始文言文",
        "modern_chinese": "白話中文",
        "target_language": "de" ,
        "translated": "德文翻譯結果"
    }

注意事項：
    1. 專案根目錄需要有 config.ini
    2. config.ini 需要包含 AzureTranslator 設定
    3. requirements.txt 需要安裝 azure-ai-translation-text 和 azure-core

    之後記得刪除這個
"""
import configparser

from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")


def get_translator_client():
    return TextTranslationClient(
        credential=AzureKeyCredential(config["AzureTranslator"]["Key"]),
        endpoint=config["AzureTranslator"]["Endpoint"],
        region=config["AzureTranslator"]["Region"],
    )


def azure_translate(text: str, target_language: str, source_language: str = None) -> str:
    if not text or not text.strip():
        return ""

    try:
        client = get_translator_client()

        response = client.translate(
            body=[text],
            to_language=[target_language],
            from_language=source_language
        )

        translation = response[0] if response else None

        if translation and translation.translations:
            return translation.translations[0].text

        return ""

    except HttpResponseError as exception:
        print(f"Azure Translator Error Code: {exception.error}")
        print(f"Message: {exception.error.message}")
        return "翻譯失敗"

    except Exception as exception:
        print(f"Unexpected Error: {exception}")
        return "翻譯失敗"


def classical_to_modern_chinese(text: str) -> str:
    return azure_translate(
        text=text,
        target_language="zh-Hant",
        source_language="lzh"
    )


def translate_poem(text: str, target_language: str = "de") -> dict:

    modern_chinese = classical_to_modern_chinese(text)

    translated = azure_translate(
        text=modern_chinese,
        target_language=target_language,
        source_language="zh-Hant"
    )

    return {
        "original": text,
        "modern_chinese": modern_chinese,
        "target_language": target_language,
        "translated": translated
    }