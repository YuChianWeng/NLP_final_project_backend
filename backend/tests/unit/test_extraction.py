import pytest
from unittest.mock import MagicMock, patch
from app.services.extraction import extract_movie_title


# --- Heuristic 括號測試（不呼叫 API）---

@pytest.mark.parametrize("message,expected", [
    ("《全面啟動》好看嗎",       "全面啟動"),
    ("「寄生上流」值得看嗎",     "寄生上流"),
    ("『你的名字』超感人",       "你的名字"),
    ('「Inception」是什麼電影',  "Inception"),
    ("【星際效應】的評分如何",   "星際效應"),
    ("[Parasite] 有中文版嗎",    "Parasite"),
])
def test_heuristic_extracts_bracketed_title(message, expected):
    result = extract_movie_title(message)
    assert result == expected


# --- LLM fallback 測試（mock Azure OpenAI）---

def _mock_completion(content: str):
    """建立假的 Azure OpenAI chat completion 回傳值。"""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("app.services.extraction._get_client")
def test_llm_extracts_title_from_plain_sentence(mock_get_client):
    mock_get_client.return_value.chat.completions.create.return_value = (
        _mock_completion("全面啟動")
    )
    result = extract_movie_title("幫我查一下全面啟動")
    assert result == "全面啟動"


@patch("app.services.extraction._get_client")
def test_llm_returns_none_when_no_movie(mock_get_client):
    mock_get_client.return_value.chat.completions.create.return_value = (
        _mock_completion("none")
    )
    result = extract_movie_title("今天天氣很好")
    assert result is None


@patch("app.services.extraction._get_client")
def test_llm_returns_none_case_insensitive(mock_get_client):
    mock_get_client.return_value.chat.completions.create.return_value = (
        _mock_completion("None")
    )
    result = extract_movie_title("我想吃晚餐")
    assert result is None


@patch("app.services.extraction._get_client")
def test_heuristic_takes_priority_over_llm(mock_get_client):
    """有括號時不應呼叫 LLM。"""
    result = extract_movie_title("《星際效應》怎麼樣")
    mock_get_client.assert_not_called()
    assert result == "星際效應"


@patch("app.services.extraction._get_client")
def test_llm_strips_whitespace_from_response(mock_get_client):
    mock_get_client.return_value.chat.completions.create.return_value = (
        _mock_completion("  寄生上流  ")
    )
    result = extract_movie_title("寄生上流好看嗎")
    assert result == "寄生上流"
