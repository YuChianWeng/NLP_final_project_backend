from typing import List
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings


def get_azure_client() -> TextAnalyticsClient:
    return TextAnalyticsClient(
        endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_LANGUAGE_API_KEY)
    )


def summarize(reviews: List[str]) -> str:
    """
    調用 Azure AI Language — Extractive Summarization 生成摘要。
    使用 begin_extract_summary + zh-Hans（UK West 區域相容，繁體字仍可正確處理）。
    """
    if not reviews:
        return "暫無評論數據，無法生成摘要。"

    client = get_azure_client()
    combined_text = "\n".join(reviews)

    try:
        poller = client.begin_extract_summary(
            [combined_text],
            max_sentence_count=5,
            language="zh-Hans",
        )

        sentences = []
        for result in poller.result():
            if not result.is_error:
                sentences.extend(s.text for s in result.sentences)

        if sentences:
            return " ".join(sentences)
        return "Azure 摘要生成未預期空值，請改用原始評論進行後續處理。"

    except Exception as e:
        raise RuntimeError(f"Azure Summarizer 服務暫時不可用，原因: {str(e)}")