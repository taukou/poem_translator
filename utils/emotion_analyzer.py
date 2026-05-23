"""
情緒分析模塊 - 使用Azure Text Analytics進行詩詞情緒分析
"""

import configparser
import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# 取得項目根目錄的 config.ini 路徑
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
config = configparser.ConfigParser()
config.read(config_path, encoding="utf-8")


class EmotionAnalyzer:
    """Azure Text Analytics情緒分析器"""
    
    def __init__(self):
        """初始化情緒分析器"""
        try:
            # 取得Azure語言服務密鑰和端點
            self.key = config.get('AZURELANGUAGE', 'AZURE_LANGUAGE_KEY')
            self.endpoint = config.get('AZURELANGUAGE', 'AZURE_LANGUAGE_ENDPOINT')
            
            # 初始化Azure Text Analytics客戶端
            self.client = TextAnalyticsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        except Exception as e:
            print(f"[ERROR] 初始化失敗: {e}")
            print(f"[DEBUG] 可用的 sections: {config.sections()}")
            print(f"[DEBUG] Config path: {config_path}")
            raise
    
    def analyze_sentiment(self, text, language="zh-Hans"):
        """
        分析文本情緒
        
        Args:
            text: 要分析的文本
            language: 語言代碼 (預設: "zh-Hans" 簡體中文)
        
        Returns:
            dict: 包含整體情緒和逐句分析的結果
        """
        try:
            # 進行情緒分析
            result = self.client.analyze_sentiment(
                documents=[text],
                language=language
            )[0]
            
            # 提取整體情緒
            overall_sentiment = result.sentiment
            overall_score = {
                "positive": result.confidence_scores.positive,
                "neutral": result.confidence_scores.neutral,
                "negative": result.confidence_scores.negative
            }
            
            print(f"整體情緒：{overall_sentiment}")
            print(f"信心分數 - 正面: {overall_score['positive']:.2%}, 中立: {overall_score['neutral']:.2%}, 負面: {overall_score['negative']:.2%}")
            print()
            
            # 逐句分析
            sentences_analysis = []
            for idx, sentence in enumerate(result.sentences):
                sentence_data = {
                    "index": idx + 1,
                    "text": sentence.text,
                    "sentiment": sentence.sentiment,
                    "scores": {
                        "positive": sentence.confidence_scores.positive,
                        "neutral": sentence.confidence_scores.neutral,
                        "negative": sentence.confidence_scores.negative
                    },
                    "opinions": []
                }
                
                # 提取意見（意見主體和其情緒）
                for opinion in sentence.mined_opinions:
                    opinion_data = {
                        "target": opinion.target.text,
                        "sentiment": opinion.sentiment,
                        "scores": {
                            "positive": opinion.confidence_scores.positive,
                            "neutral": opinion.confidence_scores.neutral,
                            "negative": opinion.confidence_scores.negative
                        }
                    }
                    sentence_data["opinions"].append(opinion_data)
                
                sentences_analysis.append(sentence_data)
                
                # 打印逐句分析結果
                opinions_str = ", ".join([f"{op['target']}({op['sentiment']})" for op in sentence_data["opinions"]])
                print(f"{idx+1}. {sentence.text}")
                print(f"   情緒：{sentence.sentiment} | 意見：{opinions_str if opinions_str else '無'}")
            
            return {
                "overall_sentiment": overall_sentiment,
                "overall_scores": overall_score,
                "sentences": sentences_analysis
            }
        
        except Exception as e:
            print(f"情緒分析出錯: {str(e)}")
            return None
    
    def analyze_emotion_with_details(self, text, language="zh-Hans"):
        """
        進行詳細的情緒分析（包含所有信息）
        
        Args:
            text: 要分析的文本
            language: 語言代碼
        
        Returns:
            dict: 詳細的分析結果
        """
        result = self.analyze_sentiment(text, language)
        
        if result is None:
            return None
        
        return {
            "success": True,
            "overall_sentiment": result["overall_sentiment"],
            "overall_scores": result["overall_scores"],
            "sentences_count": len(result["sentences"]),
            "sentences": result["sentences"]
        }
    
    def get_emotion_color(self, sentiment):
        """
        根據情緒返回對應的顏色代碼
        
        Args:
            sentiment: 情緒類型 (positive, neutral, negative)
        
        Returns:
            str: 十六進制顏色代碼
        """
        emotion_colors = {
            "positive": "#FFD700",    # 金黃色 - 喜悅
            "neutral": "#808080",     # 灰色 - 平靜
            "negative": "#4169E1"     # 皇家藍 - 悲傷
        }
        return emotion_colors.get(sentiment, "#808080")


# 使用示例
if __name__ == "__main__":
    analyzer = EmotionAnalyzer()
    
    # 示例文本
    sample_text = "這是一首很美麗的詩。我非常喜歡它。"
    
    result = analyzer.analyze_emotion_with_details(sample_text)
    print("\n=== 完整分析結果 ===")
    print(f"整體情緒：{result['overall_sentiment']}")
    print(f"句子數量：{result['sentences_count']}")
