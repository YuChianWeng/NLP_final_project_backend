from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.analysis import AspectSentiment
from app.schemas.common import SentimentResult


class ConversationRequest(BaseModel):
    """
    前端送來的對話請求
    """

    message: str = Field(
        ...,
        description="使用者輸入訊息"
    )


class ResultBundle(BaseModel):
    """
    US3 最終回傳結果
    """

    status: str = Field(
        ...,
        description="ok / no_movie_in_message / movie_not_found / insufficient_data"
    )

    matched_movie: Optional[dict] = Field(
        default=None,
        description="辨識出的電影資訊"
    )

    movie_rating: Optional[float] = Field(
        default=None,
        description="電影平均評分"
    )

    overall_sentiment: Optional[SentimentResult] = Field(
        default=None,
        description="整體情緒分析"
    )

    aspect_sentiments: List[AspectSentiment] = Field(
        default_factory=list,
        description="五大面向情緒分析"
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