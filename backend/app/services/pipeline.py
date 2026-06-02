import base64

from sqlalchemy.orm import Session

from app.schemas.bundle import ResultBundle
from app.schemas.analysis import AnalysisResult

from app.services.extraction import extract_movie_title
from app.services.repository import find_movie, get_reviews

from app.services.sentiment import (
    analyze_overall,
    analyze_by_aspect
)

from app.services.summarizer import summarize

from app.services.refiner import (
    refine_summary,
    RefinementUnavailable
)

from app.services.tts import (
    synthesize,
    TtsUnavailable
)


def build_movie_insight(
    message: str,
    db: Session
) -> ResultBundle:
    """
    US3 主流程

    使用者輸入
        ↓
    片名抽取
        ↓
    電影查詢
        ↓
    評論取得
        ↓
    情緒分析
        ↓
    摘要生成
        ↓
    GPT 潤飾
        ↓
    TTS 語音
        ↓
    ResultBundle
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
    # Step2: 查電影
    # --------------------------------------------------

    movie = find_movie(title, db)

    if not movie:
        return ResultBundle(
            status="movie_not_found",
            matched_movie=title
        )

    # --------------------------------------------------
    # Step3: 查評論
    # --------------------------------------------------

    reviews = get_reviews(movie.id, db)

    if len(reviews) == 0:
        return ResultBundle(
            status="insufficient_data",
            matched_movie=movie.canonical_title
        )

    # --------------------------------------------------
    # Step4: 整理評論資料
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

    analysis = AnalysisResult(
        overall_sentiment=overall_sentiment,
        aspect_sentiments=aspect_sentiments
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
            "summary_refinement_failed"
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
            "tts_failed"
        )

    # --------------------------------------------------
    # Step9: 回傳
    # --------------------------------------------------

    return ResultBundle(
        status="ok",
        matched_movie=movie.canonical_title,
        analysis=analysis,
        summary_text=refined_summary,
        audio_base64=audio_base64,
        audio_format=audio_format,
        warnings=warnings
    )