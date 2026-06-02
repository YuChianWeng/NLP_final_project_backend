ALLOWED_ASPECTS = {"plot", "acting", "visuals", "sound", "pacing"}


ASPECT_KEYWORDS = {
    "plot": [
        "plot", "story", "script", "screenplay", "ending", "twist",
        "narrative", "premise", "concept", "劇情", "故事", "結局", "反轉", "編劇"
    ],
    "acting": [
        "acting", "actor", "actress", "performance", "cast", "character",
        "role", "leonardo", "dicaprio", "演技", "演員", "角色", "表演", "主演"
    ],
    "visuals": [
        "visual", "visuals", "cinematography", "camera", "shot", "cgi",
        "effects", "vfx", "animation", "scene", "畫面", "攝影", "鏡頭", "特效", "動畫"
    ],
    "sound": [
        "music", "sound", "soundtrack", "score", "audio", "song",
        "hans zimmer", "配樂", "音樂", "音效", "聲音", "歌曲"
    ],
    "pacing": [
        "pacing", "pace", "slow", "boring", "rushed", "dragging",
        "tempo", "runtime", "節奏", "步調", "拖", "無聊", "太慢", "太快"
    ],
}


def classify_aspect(text: str) -> str:
    """
    根據評論文字粗略判斷 aspect。

    注意：
    Metacritic 不會直接告訴我們這則評論是在講 plot、acting 還是 visuals。
    所以第一版先用關鍵字規則判斷。
    """
    if not text:
        return "plot"

    lower_text = text.lower()

    aspect_scores = {
        "plot": 0,
        "acting": 0,
        "visuals": 0,
        "sound": 0,
        "pacing": 0,
    }

    for aspect, keywords in ASPECT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lower_text:
                aspect_scores[aspect] += 1

    best_aspect = max(aspect_scores, key=aspect_scores.get)

    if aspect_scores[best_aspect] == 0:
        return "plot"

    return best_aspect