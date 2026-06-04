import base64
from typing import List
from sqlalchemy.orm import Session

from app.schemas.bundle import ResultBundle

from app.services.scoring import average_rating

from app.services.extraction import extract_movie_title
from app.services.repository import find_movie, get_reviews
from app.services.sentiment import analyze_overall, analyze_by_aspect
from app.services.summarizer import summarize
from app.services.refiner import refine_summary, RefinementUnavailable
from app.services.tts import synthesize, TtsUnavailable

# 👈 內置一個鴨子型別物件，完美相容爬蟲原始數據與 DB 欄位語法
class CrawledReviewAdapter:
    def __init__(self, text: str, aspect: str):
        self.text = text
        self.aspect = aspect

def build_movie_insight(
    message: str,
    db: Session
) -> ResultBundle:
    """
    US3 主流程 (動態爬蟲與動態標籤分類升級版)
    """
    warnings = []

    # --------------------------------------------------
    # Step1: 抽電影名稱
    # --------------------------------------------------
    title = extract_movie_title(message)
    if not title:
        return ResultBundle(
            status="no_movie_in_message"
        )

    # --------------------------------------------------
    # Step2 & 3: 查電影與查評論 (整合即時爬蟲動態補給機制)
    # --------------------------------------------------
    movie = find_movie(title, db)
    reviews = []
    matched_title = title

    if movie:
        matched_title = movie.canonical_title
        reviews = get_reviews(movie.id, db)

    # 🚨 【核心對接邏輯】如果資料庫沒電影，或是這部電影一條評論都沒有，立刻向爬蟲組求援！
    if not movie or len(reviews) == 0:
        try:
            # 引入爬蟲組模組與其關鍵字分類器
            from crawler import get_movie_reviews
            from crawler.aspect_classifier import classify_aspect
            
            # 發動線上爬蟲抓取評論
            crawler_data = get_movie_reviews(title, limit=30)
            
            if crawler_data and crawler_data[0]["reviews"]:
                movie_packet = crawler_data[0]
                matched_title = movie_packet["canonical_title"]
                
                # 清洗並使用爬蟲組分類器打上面向標籤
                reviews = []
                for r in movie_packet["reviews"]:
                    raw_text = r.get("text", "")
                    predicted_aspect = classify_aspect(raw_text)  # 自動識別面向
                    
                    # 轉譯為具備 .text 與 .aspect 屬性的物件，確保後續舊程式完全不用改！
                    reviews.append(CrawledReviewAdapter(raw_text, predicted_aspect))
                    
                # 提示：此處可根據專案需求，調用資料庫寫入函式將新電影與 reviews 永久儲存回 DB 落地
                warnings.append("data_fetched_from_live_crawler")
                
        except Exception as crawler_error:
            # 如果連爬蟲都翻車，且資料庫原本就沒電影，才無奈宣告找不到電影
            if not movie:
                return ResultBundle(
                    status="movie_not_found",
                    matched_movie=title
                )

    # 再次檢查，如果依然空空如也，才回傳資料不足
    if len(reviews) == 0:
        return ResultBundle(
            status="insufficient_data",
            matched_movie=matched_title
        )

    # --------------------------------------------------
    # Step4: 整理評論資料 (完全保留你原本的優美清洗邏輯！)
    # --------------------------------------------------
    review_texts = [
        review.text
        for review in reviews
    ]

    reviews_with_aspect = [
        {
            "text": review.text,
            "aspect": review.aspect
        }
        for review in reviews
    ]

    # --------------------------------------------------
    # Step5: 情緒分析
    # --------------------------------------------------
    overall_sentiment = analyze_overall(
        review_texts
    )

    aspect_sentiments = analyze_by_aspect(
        reviews_with_aspect
    )

    movie_rating = average_rating(
    reviews
    )

    # --------------------------------------------------
    # Step6: 摘要生成
    # --------------------------------------------------
    try:
        raw_summary = summarize(review_texts)
    except RuntimeError:
        raw_summary = "摘要服務暫時無法使用。"
        warnings.append("summarization_failed")

    # --------------------------------------------------
    # Step7: GPT 潤飾
    # --------------------------------------------------
    try:
        refined_summary = refine_summary(
            raw_summary
        )
    except RefinementUnavailable:
        refined_summary = raw_summary
        warnings.append(
            "llm_refinement_unavailable"
        )

    # --------------------------------------------------
    # Step8: TTS
    # --------------------------------------------------
    audio_base64 = None
    audio_format = None

    try:
        audio_bytes = synthesize(
            refined_summary
        )

        audio_base64 = (
            base64.b64encode(audio_bytes)
            .decode("utf-8")
        )
        audio_format = "mp3"

    except TtsUnavailable:
        warnings.append(
            "tts_unavailable"
        )

    # --------------------------------------------------
    # Step9: 回傳
    # --------------------------------------------------
    return ResultBundle(
        status="ok",
        matched_movie=matched_title,
        analysis=analysis,
        summary_text=refined_summary,

        audio_base64=audio_base64,

        audio_format=audio_format,

        warnings=warnings
    )