import pytest
from app.services.scoring import average_rating

# 建立一個簡單的 Mock 類別來模擬資料庫查詢回來的 Review 物件
class MockReview:
    def __init__(self, rating):
        self.rating = rating

def test_average_rating_normal():
    """測試正常計算與四捨五入到小數第一位 (例如 (4+5+4)/3 = 4.333... -> 4.3)"""
    reviews = [MockReview(4), MockReview(5), MockReview(4)]
    assert average_rating(reviews) == 4.3

def test_average_rating_empty():
    """測試傳入空列表時，應安全回傳 0.0"""
    assert average_rating([]) == 0.0

def test_average_rating_with_none():
    """測試當部分評論沒有給分 (None) 時，應只計算有給分的平均 ( (5+3)/2 = 4.0 )"""
    reviews = [MockReview(5), MockReview(None), MockReview(3)]
    assert average_rating(reviews) == 4.0

def test_average_rating_with_dict():
    """測試傳入字典格式是否也能相容"""
    reviews = [{"rating": 5}, {"rating": 4}]
    assert average_rating(reviews) == 4.5