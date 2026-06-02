import pytest
from unittest.mock import MagicMock, patch
from app.services.summarizer import summarize

@patch('app.services.summarizer.get_azure_client')
def test_summarize_success_pipeline(mock_get_azure_client):
    """測試 Azure 抽象式摘要的多層複雜結構是否能順利提取文字（完美相容新舊版 SDK 屬性）"""
    mock_client = MagicMock()
    mock_poller = MagicMock()
    
    # 1. 建立最內層的真實摘要文字 Mock
    mock_summary = MagicMock()
    mock_summary.text = "這是一部充滿哲學思維的科幻神作。"
    
    # 2. 建立動作結果實體
    mock_action_result = MagicMock()
    mock_action_result.is_error = False
    
    # 🔥 關鍵防錯：同時餵飽 hasattr() 的新版與舊版檢查路徑，確保不論程式走哪一條分支都能成功解包
    # 模擬新版 SDK (直接把 summaries 放在 action_result 底下)
    mock_action_result.summaries = [mock_summary]
    
    # 模擬舊版 SDK (包裹在 documents 內)
    mock_doc = MagicMock()
    mock_doc.is_error = False
    mock_doc.summaries = [mock_summary]
    mock_action_result.documents = [mock_doc]
    
    # 3. 封裝分頁結構並綁定至工廠回傳
    mock_poller.result.return_value = [[mock_action_result]]
    mock_client.begin_analyze_actions.return_value = mock_poller
    mock_get_azure_client.return_value = mock_client
    
    # 4. 執行測試
    result = summarize(["評論1", "評論2"])
    
    # 5. 斷言驗證
    assert result == "這是一部充滿哲學思維的科幻神作。"

@patch('app.services.summarizer.get_azure_client')
def test_summarize_azure_exception_handling(mock_get_azure_client):
    """測試當 Azure 網路連線中斷或憑證失效時，是否會丟出帶有特定說明與優雅降級提示的 RuntimeError"""
    mock_client = MagicMock()
    
    # 透過精準 Mock 工廠函式，強迫真實被調用的 begin_analyze_actions 噴出網路異常
    mock_client.begin_analyze_actions.side_effect = Exception("Connection timed out")
    mock_get_azure_client.return_value = mock_client
    
    # 驗證後端服務是否確實捕獲並拋出帶有降級提示的專屬 RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        summarize(["全面啟動超好看"])
        
    assert "Azure Summarizer 服務暫時不可用" in str(exc_info.value)