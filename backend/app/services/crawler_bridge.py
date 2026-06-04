from crawler import get_movie_reviews  # 呼叫爬蟲組主入口
from crawler.aspect_classifier import classify_aspect  # 呼叫爬蟲組分類器

def fetch_and_enrich_movie_data(movie_name: str, limit: int = 60) -> dict:
    """
    對接爬蟲組，並將資料轉化為後端與資料庫完全相容的黃金格式
    """
    # 1. 啟動爬蟲抓取 Metacritic 原始評論
    raw_data = get_movie_reviews(movie_name=movie_name, limit=limit)
    
    if not raw_data:
        return {}
        
    # 爬蟲組包裝格式為 list[dict]，我們取第一部電影
    movie_packet = raw_data[0]
    
    enriched_reviews = []
    
    # 2. 進行資料清洗與結合 (將爬蟲資料加工打上 aspect 標籤)
    for review in movie_packet["reviews"]:
        raw_text = review.get("text", "")
        
        # 使用爬蟲組寫好的關鍵字大腦，自動辨識出 'plot', 'acting' 等面向
        predicted_aspect = classify_aspect(raw_text)
        
        # 組裝成完全符合你 Stream B大腦與資料庫規格的字典
        enriched_reviews.append({
            "text": raw_text,
            "rating": review.get("rating"),
            "aspect": predicted_aspect  # 👈 成功補齊關鍵地雷欄位！
        })
        
    # 更新回原本的封裝結構
    movie_packet["reviews"] = enriched_reviews
    
    return movie_packet