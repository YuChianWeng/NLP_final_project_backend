from enum import Enum
from pydantic import BaseModel, Field

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class SentimentResult(BaseModel):
    label: SentimentLabel = Field(..., description="情緒標籤")
    confidence: float = Field(..., description="情緒信心值 (0.0 - 1.0)", ge=0.0, le=1.0)