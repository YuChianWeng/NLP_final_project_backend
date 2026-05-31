from typing import List, Dict
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from app.config import settings  # 載入 T005 的金鑰與端點
from app.schemas.common import SentimentResult, SentimentLabel  # 載入 T008
from app.schemas.analysis import AspectSentiment  # 載入 T020
from app.lib.aspects import ASPECT_MAP  # 載入 T007

# 1. 初始化 Azure AI Language 客戶端
def get_azure_client() -> TextAnalyticsClient:
    return TextAnalyticsClient(
        endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_LANGUAGE_API_KEY)
    )

def analyze_overall(reviews: List[str]) -> SentimentResult:
    """
    調用 Azure AI Language 分析電影的整體綜合情緒
    """
    if not reviews:
        return SentimentResult(label=SentimentLabel.NEUTRAL, confidence=1.0)
        
    client = get_azure_client()
    
    # 規格書決策：將所有評論聚合成一個大文本進行整體情緒評估
    combined_text = "\n".join(reviews)
    
    try:
        response = client.analyze_sentiment(documents=[combined_text], language="zh-Hant")
        doc = response[0]
        
        if doc.is_error:
            return SentimentResult(label=SentimentLabel.NEUTRAL, confidence=1.0)
            
       # 轉換 Azure 標籤至 Pydantic Enum
        azure_label = doc.sentiment
        label_map = {
            "positive": SentimentLabel.POSITIVE,
            "neutral": SentimentLabel.NEUTRAL,
            "negative": SentimentLabel.NEGATIVE,
            "mixed": SentimentLabel.NEUTRAL  # 混合情緒對應至中立
        }
        mapped_label = label_map.get(azure_label, SentimentLabel.NEUTRAL)
        
        # 🟢 優化信心值提取邏輯
        if azure_label == "mixed":
            # 對於混合情緒，取正向或負向中得分最高者，反映其情緒強烈度，避免呈現 0.0
            confidence = max(doc.confidence_scores.positive, doc.confidence_scores.negative)
        else:
            confidence = getattr(doc.confidence_scores, azure_label)
        
        return SentimentResult(label=mapped_label, confidence=round(confidence, 2))
        
    except Exception:
        # 發生非預期錯誤時，依據優雅降級原則回傳安全中立值
        return SentimentResult(label=SentimentLabel.NEUTRAL, confidence=1.0)

def analyze_by_aspect(reviews_with_aspect: List[Dict[str, str]]) -> List[AspectSentiment]:
    """
    嚴格遵循規格書：依面向分組後，各跑一次 Azure 情緒分析（不啟用 Opinion Mining）
    """
    client = get_azure_client()
    
    # 本地分組邏輯
    grouped_reviews: Dict[str, List[str]] = {aspect_code: [] for aspect_code in ASPECT_MAP.keys()}
    for review in reviews_with_aspect:
        aspect_code = review.get("aspect")
        review_text = review.get("text")
        if aspect_code in grouped_reviews and review_text:
            grouped_reviews[aspect_code].append(review_text)
            
    aspect_results: List[AspectSentiment] = []
    
    # 逐一面向調用 Azure
    for aspect_code, aspect_chinese in ASPECT_MAP.items():
        texts = grouped_reviews[aspect_code]
        review_count = len(texts)
        
        if review_count > 0:
            combined_aspect_text = "\n".join(texts)
            try:
                response = client.analyze_sentiment(documents=[combined_aspect_text], language="zh-Hant")
                doc = response[0]
                
                if not doc.is_error:
                    azure_label = doc.sentiment
                    label_map = {"positive": SentimentLabel.POSITIVE, "neutral": SentimentLabel.NEUTRAL, "negative": SentimentLabel.NEGATIVE, "mixed": SentimentLabel.NEUTRAL}
                    mapped_label = label_map.get(azure_label, SentimentLabel.NEUTRAL)
                    confidence = getattr(doc.confidence_scores, azure_label if azure_label != "mixed" else "neutral")
                    
                    sentiment_res = SentimentResult(label=mapped_label, confidence=round(confidence, 2))
                else:
                    sentiment_res = SentimentResult(label=SentimentLabel.NEUTRAL, confidence=1.0)
            except Exception:
                sentiment_res = SentimentResult(label=SentimentLabel.NEUTRAL, confidence=1.0)
        else:
            # 查無評論時的預設中立欄位
            sentiment_res = SentimentResult(label=SentimentLabel.NEUTRAL, confidence=1.0)
            
        aspect_results.append(AspectSentiment(
            aspect=aspect_code,
            aspect_display=aspect_chinese,
            sentiment=sentiment_res,
            review_count=review_count
        ))
        
    return aspect_results