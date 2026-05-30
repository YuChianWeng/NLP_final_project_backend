from unittest.mock import MagicMock, patch
from app.services.sentiment import analyze_overall, analyze_by_aspect
from app.schemas.common import SentimentLabel

@patch('app.services.sentiment.TextAnalyticsClient')
def test_analyze_overall_success(mock_client_class):
    """測試整體情緒分析成功時的標籤轉換與數值四捨五入"""
    # 1. 建立虛擬的 Azure 回傳文件物件
    mock_client = MagicMock()
    mock_doc = MagicMock()
    mock_doc.is_error = False
    mock_doc.sentiment = "positive"
    mock_doc.confidence_scores.positive = 0.866
    
    # 2. 綁定 Mock 鏈結
    mock_client.analyze_sentiment.return_value = [mock_doc]
    mock_client_class.return_value = mock_client
    
    # 3. 執行測試
    result = analyze_overall(["這部電影特效超讚！", "劇情很感人。"])
    
    # 4. 斷言驗證
    assert result.label == SentimentLabel.POSITIVE
    assert result.confidence == 0.87  # 驗證是否有 round(..., 2)

@patch('app.services.sentiment.TextAnalyticsClient')
def test_analyze_overall_empty_or_error_fallback(mock_client_class):
    """測試傳入空評論或 Azure 噴錯時，是否優雅降級為 neutral"""
    # 測試空評論
    empty_result = analyze_overall([])
    assert empty_result.label == SentimentLabel.NEUTRAL
    assert empty_result.confidence == 1.0

    # 測試 Azure 回傳錯誤文件
    mock_client = MagicMock()
    mock_doc = MagicMock()
    mock_doc.is_error = True
    mock_client.analyze_sentiment.return_value = [mock_doc]
    mock_client_class.return_value = mock_client
    
    error_result = analyze_overall(["測試噴錯文字"])
    assert error_result.label == SentimentLabel.NEUTRAL

@patch('app.services.sentiment.TextAnalyticsClient')
def test_analyze_by_aspect_grouping(mock_client_class):
    """測試五大面向是否正確分組並逐一調用 Azure"""
    mock_client = MagicMock()
    mock_doc = MagicMock()
    mock_doc.is_error = False
    mock_doc.sentiment = "negative"
    mock_doc.confidence_scores.negative = 0.95
    mock_client.analyze_sentiment.return_value = [mock_doc]
    mock_client_class.return_value = mock_client
    
    # 傳入已標記面向的測試評論
    test_reviews = [
        {"text": "特效很假", "aspect": "visuals"},
        {"text": "配樂太小聲", "aspect": "music"},
        {"text": "特效動畫不及格", "aspect": "visuals"}
    ]
    
    results = analyze_by_aspect(test_reviews)
    
    # 斷言驗證：固定回傳五大面向結果
    assert len(results) == 5
    
    # 檢查有評論的面向 (visuals) 是否正確統計數量
    visuals_res = next(r for r in results if r.aspect == "visuals")
    assert visuals_res.review_count == 2
    assert visuals_res.sentiment.label == SentimentLabel.NEGATIVE
    
    # 檢查沒評論的面向 (plot) 是否優雅給予中立預設值
    plot_res = next(r for r in results if r.aspect == "plot")
    assert plot_res.review_count == 0
    assert plot_res.sentiment.label == SentimentLabel.NEUTRAL