from unittest.mock import patch

from app.services.pipeline import build_movie_insight
from app.schemas.common import (
    SentimentResult,
    SentimentLabel
)


class MockMovie:
    id = 1
    canonical_title = "復仇者聯盟"


class MockReview:
    def __init__(self):
        self.text = "很好看"
        self.aspect = "plot"


def test_no_movie_in_message():

    with patch(
        "app.services.pipeline.extract_movie_title",
        return_value=None
    ):

        result = build_movie_insight(
            "你好",
            None
        )

    assert result.status == "no_movie_in_message"


def test_movie_not_found():

    with patch(
        "app.services.pipeline.extract_movie_title",
        return_value="復仇者聯盟"
    ), patch(
        "app.services.pipeline.find_movie",
        return_value=None
    ):

        result = build_movie_insight(
            "復仇者聯盟",
            None
        )

    assert result.status == "movie_not_found"
    assert result.matched_movie == "復仇者聯盟"


def test_insufficient_data():

    movie = MockMovie()

    with patch(
        "app.services.pipeline.extract_movie_title",
        return_value="復仇者聯盟"
    ), patch(
        "app.services.pipeline.find_movie",
        return_value=movie
    ), patch(
        "app.services.pipeline.get_reviews",
        return_value=[]
    ):

        result = build_movie_insight(
            "復仇者聯盟",
            None
        )

    assert result.status == "insufficient_data"
    assert result.matched_movie == movie.canonical_title


def test_ok():

    movie = MockMovie()

    reviews = [
        MockReview()
    ]

    overall_sentiment = SentimentResult(
        label=SentimentLabel.POSITIVE,
        confidence=0.95
    )

    with patch(
        "app.services.pipeline.extract_movie_title",
        return_value="復仇者聯盟"
    ), patch(
        "app.services.pipeline.find_movie",
        return_value=movie
    ), patch(
        "app.services.pipeline.get_reviews",
        return_value=reviews
    ), patch(
        "app.services.pipeline.analyze_overall",
        return_value=overall_sentiment
    ), patch(
        "app.services.pipeline.analyze_by_aspect",
        return_value=[]
    ), patch(
        "app.services.pipeline.summarize",
        return_value="原始摘要"
    ), patch(
        "app.services.pipeline.refine_summary",
        return_value="潤飾後摘要"
    ), patch(
        "app.services.pipeline.synthesize",
        return_value=b"fake_audio"
    ):

        result = build_movie_insight(
            "復仇者聯盟",
            None
        )

    assert result.status == "ok"
    assert result.matched_movie == movie.canonical_title
    assert result.summary_text == "潤飾後摘要"
    assert result.audio_base64 is not None
    assert result.audio_format == "mp3"
    assert result.warnings == []