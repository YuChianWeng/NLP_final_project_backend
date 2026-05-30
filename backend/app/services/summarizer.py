from typing import List
from azure.ai.textanalytics import TextAnalyticsClient, AbstractiveSummaryAction
from azure.core.credentials import AzureKeyCredential
from app.config import settings  # 載入 T005

def get_azure_client() -> TextAnalyticsClient:
    return TextAnalyticsClient(
        endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_LANGUAGE_API_KEY)
    )

def summarize(reviews: List[str]) -> str:
    """
    調用 Azure AI Language — Document Summarization (Abstractive) 生成繁體中文摘要
    """
    if not reviews:
        return "暫無評論數據，無法生成摘要。"
        
    client = get_azure_client()
    combined_text = "\n".join(reviews)
    
    try:
        # 建立 Azure 抽象式摘要的動作規劃
        action = AbstractiveSummaryAction(language="zh-Hant")
        
        # 發起異步長週期任務
        poller = client.begin_analyze_actions(
            documents=[combined_text],
            actions=[action]
        )
        
        # 等待微軟雲端計算完成並獲取結果
        result_pages = poller.result()
        
        summary_text = ""
        for page in result_pages:
            for action_result in page:
                if action_result.is_error:
                    continue
                
                # 🔥 彈性相容性檢查：如果 SDK 已經扁平化直接吐出摘要結果
                if hasattr(action_result, "summaries"):
                    summary_text += "".join([summary.text for summary in action_result.summaries])
                
                # 如果 SDK 保留傳統結構，外層依舊是 Action 容器
                elif hasattr(action_result, "documents"):
                    for doc in action_result.documents:
                        if not doc.is_error and hasattr(doc, "summaries"):
                            summary_text += "".join([summary.text for summary in doc.summaries])
                            
        if summary_text:
            return summary_text
        return "Azure 摘要生成未預期空值，請改用原始評論進行後續處理。"
        
    except Exception as e:
        # 優雅降級：若 Azure 雲端異常，直接拋出 RuntimeError 讓 Pipeline 捕獲並退回原始文字
        raise RuntimeError(f"Azure Summarizer 服務暫時不可用，原因: {str(e)}")