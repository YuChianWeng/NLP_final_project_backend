import re


def clean_text(text: str) -> str:
    """
    清理評論文字。

    功能：
    1. 移除 spoiler alert 提示
    2. 移除 report_review / report-review 類型雜訊
    3. 把換行符號改成空白
    4. 把連續空白壓成一個空白
    5. 去掉前後空白
    """
    if not text:
        return ""

    # 移除 spoiler alert 提示，但保留後面的評論內容
    text = re.sub(
        r"\[\s*SPOILER\s+ALERT\s*:?\s*This\s+review\s+contains\s+spoilers\.?\s*\]",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # 移除 report_review / report-review / report review 這類按鈕文字
    text = re.sub(
        r"\breport[-_\s]?review(?:\s+report)?\b",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()