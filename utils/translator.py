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
