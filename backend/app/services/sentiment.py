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
        return SentimentResult(label=SentimentLabel.NEUTRAL.value, confidence=1.0)
        
    client = get_azure_client()
    
    # 規格書決策：將所有評論聚合成一個大文本進行整體情緒評估
    combined_text = "\n".join(reviews)
    
    try:
        # 🛠️ 【修正 1】整體情緒分析語系同步改為 "en"，精準辨識 Metacritic 全英文原始評論
        response = client.analyze_sentiment(documents=[combined_text], language="en")
        doc = response[0]
        
        if doc.is_error:
            return SentimentResult(label=SentimentLabel.NEUTRAL.value, confidence=1.0)
            
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
        
        # 🛠️ 【修正 2】加上 .value！將 Enum 轉換為純字串 ("positive"/"neutral"/"negative") 傳給前端
        return SentimentResult(label=mapped_label.value, confidence=round(confidence, 2))
        
    except Exception:
        # 發生非預期錯誤時，依據優雅降級原則回傳安全中立值
        return SentimentResult(label=SentimentLabel.NEUTRAL.value, confidence=1.0)

def analyze_by_aspect(reviews_with_aspect: List[Dict[str, str]]) -> List[AspectSentiment]:
    """
    優化完全體：改採「投票制（Voting）」逐則評估，完美解決長文本正負情緒互沖導致集體中立的問題
    """
    client = get_azure_client()
    
    # 1. 本地分組邏輯
    grouped_reviews: Dict[str, List[str]] = {aspect_code: [] for aspect_code in ASPECT_MAP.keys()}
    for review in reviews_with_aspect:
        aspect_code = review.get("aspect")
        review_text = review.get("text")
        if aspect_code in grouped_reviews and review_text:
            grouped_reviews[aspect_code].append(review_text)
            
    aspect_results: List[AspectSentiment] = []
    
    # 2. 逐一面向進行「民主投票」
    for aspect_code, aspect_chinese in ASPECT_MAP.items():
        texts = grouped_reviews[aspect_code]
        review_count = len(texts)
        
        if review_count > 0:
            # 建立投票箱
            votes = {"positive": 0, "neutral": 0, "negative": 0}
            confidence_accumulator = {"positive": [], "neutral": [], "negative": []}
            
            try:
                # 為了避免長文互沖，我們逐一投餵給 Azure（上限 10 則以兼顧效能與精準度）
                sample_texts = texts[:10]  
                
                # 調用 Azure 批次分析（FastAPI 支援直接傳入清單，效率極高）
                response = client.analyze_sentiment(documents=sample_texts, language="en")
                
                for doc in response:
                    if not doc.is_error:
                        label = doc.sentiment  # "positive", "neutral", "negative", or "mixed"
                        
                        # 如果個別評論被判定為 mixed，我們直接拆解看它是偏正還是偏負
                        if label == "mixed":
                            if doc.confidence_scores.positive >= doc.confidence_scores.negative:
                                actual_label = "positive"
                            else:
                                actual_label = "negative"
                        else:
                            actual_label = label
                            
                        # 投下一票
                        if actual_label in votes:
                            votes[actual_label] += 1
                            conf_score = getattr(doc.confidence_scores, actual_label)
                            confidence_accumulator[actual_label].append(conf_score)
                
                # 3. 開票階段：找出得票數最高的標籤作為最終贏家
                winner_label = max(votes, key=votes.get)
                
                # 如果最高票數為 0（例如全出錯），則預設中立
                if votes[winner_label] == 0:
                    winner_label = "neutral"
                    avg_confidence = 1.0
                else:
                    # 計算贏家標籤的平均信心值
                    scores = confidence_accumulator[winner_label]
                    avg_confidence = sum(scores) / len(scores) if scores else 1.0
                
                # 對齊 Pydantic Enum 轉換為純字串值
                label_map = {
                    "positive": SentimentLabel.POSITIVE.value,
                    "neutral": SentimentLabel.NEUTRAL.value,
                    "negative": SentimentLabel.NEGATIVE.value
                }
                final_label_str = label_map.get(winner_label, SentimentLabel.NEUTRAL.value)
                
                sentiment_res = SentimentResult(label=final_label_str, confidence=round(avg_confidence, 2))
                
            except Exception:
                sentiment_res = SentimentResult(label=SentimentLabel.NEUTRAL.value, confidence=1.0)
        else:
            # 查無評論時的預設中立
            sentiment_res = SentimentResult(label=SentimentLabel.NEUTRAL.value, confidence=1.0)
            
        aspect_results.append(AspectSentiment(
            aspect=aspect_code,
            aspect_display=aspect_chinese,
            sentiment=sentiment_res,
            review_count=review_count
        ))
        
    return aspect_results