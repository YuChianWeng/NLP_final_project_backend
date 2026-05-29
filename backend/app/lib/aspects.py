# 規格書定義之固定五大面向
ASPECT_MAP = {
    "plot": "劇情",
    "acting": "演技",
    "visuals": "視覺·特效",
    "music": "音效·配樂",
    "pacing": "節奏"
}

def get_aspect_display(aspect_code: str) -> str:
    """輸入英文代碼（如 'plot'），回傳中文顯示名稱（如 '劇情'）"""
    return ASPECT_MAP.get(aspect_code, "未知面向")