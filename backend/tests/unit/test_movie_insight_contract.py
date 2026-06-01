from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_movie_insight_contract():

    mock_response = {
        "status": "ok",
        "matched_movie": "復仇者聯盟",
        "analysis": None,
        "summary_text": "潤飾後摘要",
        "audio_base64": "ZmFrZV9hdWRpbw==",
        "audio_format": "mp3",
        "warnings": []
    }

    with patch(
        "app.api.route.build_movie_insight",
        return_value=mock_response
    ):

        response = client.post(
            "/api/v1/movie-insight",
            json={
                "message": "復仇者聯盟"
            }
        )

    assert response.status_code == 200

    body = response.json()

    assert "status" in body
    assert "matched_movie" in body
    assert "analysis" in body
    assert "summary_text" in body
    assert "audio_base64" in body
    assert "audio_format" in body
    assert "warnings" in body