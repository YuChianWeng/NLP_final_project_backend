import re
import unicodedata


def normalize(title: str) -> str:
    """casefold + 去除空白、標點、括號，用於片名比對。"""
    title = title.casefold()
    title = unicodedata.normalize("NFKC", title)
    title = re.sub(r"[\s\-_]+", "", title)
    title = re.sub(r"[^\w一-鿿]", "", title)
    return title
