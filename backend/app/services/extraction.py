import re
from openai import AzureOpenAI
from app.config import settings

_BRACKET_PATTERN = re.compile(r"[《〈「『【\[\"](.*?)[》〉」』】\]\"]")

_client: AzureOpenAI | None = None


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version="2024-02-01",
        )
    return _client


def _heuristic(message: str) -> str | None:
    """從括號（《》「」等）快速抽取片名，不呼叫 API。"""
    match = _BRACKET_PATTERN.search(message)
    return match.group(1).strip() if match else None


def _llm_extract(message: str) -> str | None:
    """用 Azure OpenAI 從自然語句抽出片名；沒有電影時回傳 None。"""
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一個電影片名抽取工具。"
                    "從使用者的句子中找出電影片名，只回傳片名本身，不加任何說明。"
                    "如果句子中沒有提到任何電影，只回傳英文單字 none。"
                ),
            },
            {"role": "user", "content": message},
        ],
    )
    result = response.choices[0].message.content.strip()
    return None if result.lower() == "none" else result


def extract_movie_title(message: str) -> str | None:
    """從對話訊息抽出電影片名。先用 heuristic，失敗再呼叫 LLM。"""
    title = _heuristic(message)
    if title:
        return title
    return _llm_extract(message)
