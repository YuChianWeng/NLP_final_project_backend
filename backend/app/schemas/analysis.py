from typing import List
from pydantic import BaseModel, Field
from app.schemas.common import SentimentResult  # 正確依賴 T008 的共用情緒結構

class AspectSentiment(BaseModel):
    """
    特定面向的情緒分析結果結構
    """
    aspect: str = Field(
        ..., 
        description="面向代碼，固定為五大面向之一：'plot' (劇情), 'acting' (演技), 'visual' (視覺效果), 'sound' (音效配樂), 'pacing' (節奏)"
    )
    aspect_display: str = Field(
        ..., 
        description="面向的繁體中文顯示名稱，例如 '劇情'、'演技'"
    )
    sentiment: SentimentResult = Field(
        ..., 
        description="該面向經由分析後得到的整體情緒標籤與信心值分數"
    )
    review_count: int = Field(
        default=0, 
        description="本地資料庫中參與該面向計算與分組的有效評論總總數"
    )

class AnalysisResult(BaseModel):
    """
    Stream B 分析核心輸出的完整結果結構
    """
    overall_sentiment: SentimentResult = Field(
        ..., 
        description="該部電影所有評論的整體綜合情緒分析結果"
    )
    aspect_sentiments: List[AspectSentiment] = Field(
        default_factory=list, 
        description="五大面向獨立計算後的情緒分析清單"
    )