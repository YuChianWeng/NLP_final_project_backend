import pytest
from unittest.mock import MagicMock
from azure.ai.textanalytics import TextAnalyticsClient  # 引入微軟官方類別
from app.services.summarizer import summarize

def test_summarize_success_pipeline(monkeypatch):
    """精準 Mock 萃取式摘要 begin_extract_summary，徹底破除 main 宇宙集體執行的快取污染"""
    # 1. 建立真實被調用的 Poller 物件
    mock_poller = MagicMock()
    
    # 2. 建立萃取式摘要最內層的句子文字 Mock (必須擁有 .text 屬性)
    mock_sentence = MagicMock()
    mock_sentence.text = "這是一部充滿哲學思維的科幻神作。"
    
    # 3. 建立符合 Extractive 規範的單個結果物件 (包含 is_error 與 sentences)
    mock_result = MagicMock()
    mock_result.is_error = False
    mock_result.sentences = [mock_sentence]
    
    # 4. 根據真實的 begin_extract_summary 規範，poller.result() 回傳的是單層可迭代清單
    # 這樣能完美對齊 for result in poller.result() 迴圈，絕不噴出 'list' object 錯誤
    mock_poller.result.return_value = [mock_result]
    
    # 🔥 【精準獵殺】直接將微軟 SDK 類別本體的進攻目標更換為最新的 begin_extract_summary
    monkeypatch.setattr(TextAnalyticsClient, "begin_extract_summary", lambda self, *args, **kwargs: mock_poller)
    
    # 5. 執行測試
    result = summarize(["評論1", "評論2"])
    
    # 6. 斷言驗證
    assert result == "這是一部充滿哲學思維的科幻神作。"


def test_summarize_azure_exception_handling(monkeypatch):
    """測試當萃取式摘要網路連線中斷時，是否能精準激發優雅降級的 RuntimeError"""
    def mock_begin_extract_summary_raise(self, *args, **kwargs):
        raise Exception("Connection timed out")
        
    # 🔥 同步全域淨化異常測試的攔截點
    monkeypatch.setattr(TextAnalyticsClient, "begin_extract_summary", mock_begin_extract_summary_raise)
    
    # 驗證後端服務是否確實捕獲異常並重組拋出
    with pytest.raises(RuntimeError) as exc_info:
        summarize(["全面啟動超好看"])
        
    assert "Azure Summarizer 服務暫時不可用" in str(exc_info.value)
    
