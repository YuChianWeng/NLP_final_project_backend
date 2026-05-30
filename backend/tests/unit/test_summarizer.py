import pytest
from unittest.mock import MagicMock, patch
from app.services.summarizer import summarize

@patch('app.services.summarizer.TextAnalyticsClient')
def test_summarize_success_pipeline(mock_client_class):
    """測試 Azure 抽象式摘要的多層複雜結構是否能順利提取文字"""
    mock_client = MagicMock()
    mock_poller = MagicMock()
    
    # 模擬最內層的摘要文字物件
    mock_summary = MagicMock()
    mock_summary.text = "這是一部充滿哲學思維的科幻神作。"
    
    # 模擬文件層
    mock_doc = MagicMock()
    mock_doc.is_error = False
    mock_doc.summaries = [mock_summary]
    
    # 模擬動作層
    mock_action_result = MagicMock()
    mock_action_result.is_error = False
    mock_action_result.documents = [mock_doc]
    
    # 模擬分頁解包（Pages -> ActionResults）
    mock_page = [mock_action_result]
    mock_poller.result.return_value = [mock_page]
    
    # 綁定至客戶端
    mock_client.begin_analyze_actions.return_value = mock_poller
    mock_client_class.return_value = mock_client
    
    # 執行測試
    result = summarize(["評論1", "評論2"])
    
    # 驗證結果
    assert result == "這是一部充滿哲學思維的科幻神作。"

@patch('app.services.summarizer.TextAnalyticsClient')
def test_summarize_azure_exception_handling(mock_client_class):
    """測試當 Azure 網路連線中斷或憑證失效時，是否會丟出帶有特定說明的 RuntimeError"""
    mock_client = MagicMock()
    # 模擬連線異常
    mock_client.begin_analyze_actions.side_effect = Exception("Connection timed out")
    mock_client_class.return_value = mock_client
    
    # 驗證是否拋出規格書要求的優雅降級異常
    with pytest.raises(RuntimeError) as exc_info:
        summarize(["全面啟動超好看"])
        
    assert "Azure Summarizer 服務暫時不可用" in str(exc_info.value)