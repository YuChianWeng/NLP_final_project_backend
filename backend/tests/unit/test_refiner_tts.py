from unittest.mock import patch

from app.services.pipeline import build_movie_insight

from app.services.refiner import (
    RefinementUnavailable
)

from app.services.tts import (
    TtsUnavailable
)

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


def test_refiner_failure():

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
        side_effect=RefinementUnavailable(
            "azure failed"
        )
    ), patch(
        "app.services.pipeline.synthesize",
        return_value=b"fake_audio"
    ):

        result = build_movie_insight(
            "復仇者聯盟",
            None
        )

    assert result.status == "ok"

    assert (
        result.summary_text
        == "原始摘要"
    )

    assert (
        "summary_refinement_failed"
        in result.warnings
    )


def test_tts_failure():

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
        side_effect=TtsUnavailable(
            "tts failed"
        )
    ):

        result = build_movie_insight(
            "復仇者聯盟",
            None
        )

    assert result.status == "ok"

    assert result.audio_base64 is None

    assert result.audio_format is None

    assert (
        "tts_failed"
        in result.warnings
    )