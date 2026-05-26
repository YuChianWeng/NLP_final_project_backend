# Quickstart: Movie Review Sentiment & Narration Service

**Feature**: `001-movie-sentiment-api` | **Date**: 2026-05-26

## Prerequisites

- Python 3.11+
- Azure resources (keys/endpoints): **AI Language** (sentiment + summarization),
  **Azure OpenAI** (LLM refinement + title extraction), **AI Speech** (TTS).

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in the Azure keys/endpoints below
```

`.env` keys:

```
AZURE_LANGUAGE_ENDPOINT=
AZURE_LANGUAGE_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_DEPLOYMENT=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
TTS_VOICE=zh-TW-HsiaoChenNeural
DATABASE_URL=sqlite:///./movies.db
```

## Initialize + seed the database

```bash
python -m app.db.seed     # creates tables and loads sample movies/reviews
```

## Run

```bash
uvicorn app.main:app --reload
```

## Smoke test (golden path)

```bash
curl -s -X POST http://localhost:8000/api/v1/movie-insight \
  -H 'Content-Type: application/json' \
  -d '{"message":"幫我查看看全面啟動這部電影"}' | jq
```

Expect `status: "ok"` with `movie_rating` (1–5), `overall_sentiment`, five
`aspect_sentiments`, `summary_text`, and `audio_base64`.

Save and play the audio:

```bash
curl -s -X POST http://localhost:8000/api/v1/movie-insight \
  -H 'Content-Type: application/json' -d '{"message":"幫我查全面啟動"}' \
  | jq -r .audio_base64 | base64 -d > out.mp3
```

## Edge-case checks

| Input | Expected `status` |
|-------|-------------------|
| `{"message":"今天天氣如何"}` | `no_movie_in_message` |
| `{"message":"幫我查一部不存在的電影XYZ"}` | `movie_not_found` |
| `{"message":""}` | HTTP 400 |
| (movie with no reviews) | `insufficient_data` |

## Tests

```bash
pytest tests/unit                       # per-stream, fully mocked (no Azure needed)
pytest tests/contract                   # request/response schema conformance
RUN_AZURE=1 pytest tests/integration    # live Azure calls (env-gated)
```

## Per-stream local dev (3 people, in parallel)

- **Stream A**: `pytest tests/unit/test_extraction.py tests/unit/test_repository.py`
- **Stream B**: `pytest tests/unit/test_sentiment.py tests/unit/test_summarizer.py tests/unit/test_scoring.py`
- **Stream C**: `pytest tests/unit/test_pipeline.py tests/unit/test_refiner.py tests/unit/test_tts.py`

Each stream mocks the others via the signatures in `contracts/internal-services.md`.
