from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisResult  # 👈 確保引入大包裹結構
from app.schemas.common import SentimentResult

class ConversationRequest(BaseModel):
    """
    前端送來的對話請求
    """
    message: str = Field(..., description="使用者輸入訊息")


class ResultBundle(BaseModel):
    """
    US3 最終回傳結果規格書（完美銜接後端 pipeline.py 與前端網頁 script.js 的擺盤）
    """
    status: str = Field(
        ...,
        description="ok / no_movie_in_message / movie_not_found / insufficient_data"
    )

    # 🟢 電影名稱明確定義為 Optional[str]（純字串），絕不引發 dict_type 驗證錯誤
    matched_movie: Optional[str] = Field(
        default=None,
        description="辨識出的電影資訊"
    )

    # 🟢 欄位更正：將 movie_rating 改為 rating，精準對齊前端渲染代碼 data.rating！
    rating: Optional[float] = Field(
        default=None,
        description="電影平均評分"
    )

    # 🟢 【核心回歸】補回 analysis 大包裹欄位，讓前端可以用 data.analysis.overall_sentiment
    # 順暢讀取各面向與綜合極性，徹底終結「未知 (信心度: 0%)」的夢魘！
    analysis: Optional[AnalysisResult] = Field(
        default=None,
        description="Stream B 綜合與各面向情緒分析完整大禮包"
    )

    summary_text: Optional[str] = Field(
        default=None,
        description="潤飾後摘要"
    )

    audio_base64: Optional[str] = Field(
        default=None,
        description="MP3 Base64 字串"
    )

    audio_format: Optional[str] = Field(
        default=None,
        description="音訊格式(mp3)"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="降級或警告訊息"
    )