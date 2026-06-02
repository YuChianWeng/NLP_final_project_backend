from openai import AzureOpenAI

from app.config import settings


class RefinementUnavailable(Exception):
    """摘要潤飾服務不可用"""
    pass


def refine_summary(summary: str) -> str:
    """
    將原始摘要潤飾成較自然的繁體中文
    """

    if not summary:
        raise RefinementUnavailable("empty summary")

    try:
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2024-12-01-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是電影評論摘要助手。"
                        "請使用繁體中文，保留原意，"
                        "將文字潤飾成自然流暢的一段摘要。"
                    )
                },
                {
                    "role": "user",
                    "content": summary
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        raise RefinementUnavailable(str(e))