from typing import List, Any

def average_rating(reviews: List[Any]) -> float:
    """
    計算電影評論的平均評分。
    
    :param reviews: 評論物件列表 (可以是 SQLAlchemy Model 或 Dict)
    :return: 平均分數，四捨五入至小數點第一位 (float)。若無有效評分則回傳 0.0。
    """
    if not reviews:
        return 0.0
        
    total_score = 0.0
    valid_count = 0
    
    for review in reviews:
        # 兼容物件屬性 (SQLAlchemy Model) 與字典 (Dict) 的取值方式
        rating = review.rating if hasattr(review, 'rating') else review.get('rating')
        
        # 確保評分存在且為數值類型
        if rating is not None and isinstance(rating, (int, float)):
            total_score += rating
            valid_count += 1
            
    if valid_count == 0:
        return 0.0
        
    avg = total_score / valid_count
    return round(avg, 1)