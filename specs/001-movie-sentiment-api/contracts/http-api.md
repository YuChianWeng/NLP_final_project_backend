# HTTP API Contract

**Feature**: `001-movie-sentiment-api` | **Date**: 2026-05-26

The frontend sends one message and receives one self-contained bundle (FR-020, FR-018).

---

## POST /api/v1/movie-insight

### Request

```json
{
  "message": "幫我查看看全面啟動這部電影"
}
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `message` | string | yes | non-empty, free-form conversational text |

### Response 200 — success (`status: "ok"`)

```json
{
  "status": "ok",
  "matched_movie": { "id": 1, "canonical_title": "全面啟動" },
  "movie_rating": 4.3,
  "overall_sentiment": { "label": "positive", "confidence": 0.87 },
  "aspect_sentiments": [
    { "aspect": "plot",    "aspect_display": "劇情",     "sentiment": { "label": "positive", "confidence": 0.91 }, "review_count": 4 },
    { "aspect": "acting",  "aspect_display": "演技",     "sentiment": { "label": "positive", "confidence": 0.80 }, "review_count": 3 },
    { "aspect": "visuals", "aspect_display": "視覺/特效", "sentiment": { "label": "positive", "confidence": 0.95 }, "review_count": 5 },
    { "aspect": "sound",   "aspect_display": "音效/配樂", "sentiment": { "label": "neutral",  "confidence": 0.60 }, "review_count": 2 },
    { "aspect": "pacing",  "aspect_display": "節奏",     "sentiment": { "label": "negative", "confidence": 0.72 }, "review_count": 2 }
  ],
  "summary_text": "這部電影在視覺與劇情上表現突出……",
  "audio_base64": "<base64 mp3>",
  "audio_format": "mp3",
  "warnings": []
}
```

### Response 200 — degraded enrichment

Enrichment failures do NOT fail the request (FR-018, FR-021, SC-006). Core fields stay
populated; skipped parts are null and listed in `warnings`.

```json
{
  "status": "ok",
  "matched_movie": { "id": 1, "canonical_title": "全面啟動" },
  "movie_rating": 4.3,
  "overall_sentiment": { "label": "positive", "confidence": 0.87 },
  "aspect_sentiments": [ "...": "as above" ],
  "summary_text": "原始 Azure 摘要文字……",
  "audio_base64": null,
  "audio_format": null,
  "warnings": ["llm_refinement_unavailable", "tts_unavailable"]
}
```

### Response 200 — non-success outcomes (still HTTP 200)

| `status` | Meaning | Populated fields |
|----------|---------|------------------|
| `no_movie_in_message` | No movie title found in the text (FR-003) | `status`, `warnings`, human-readable `message_zh` prompt |
| `movie_not_found` | Title extracted but no DB match (FR-007) | `status`, `extracted_title`, `message_zh` |
| `insufficient_data` | Movie matched but has zero reviews (FR-015) | `status`, `matched_movie`, `message_zh` |

```json
{ "status": "movie_not_found", "extracted_title": "不存在的電影", "message_zh": "找不到這部電影,請換一部試試。", "warnings": [] }
```

### Response 400

Empty/whitespace `message` or malformed body.

```json
{ "detail": "message must not be empty" }
```

### Response 502 / 503

Only when a **core** stage (sentiment, summarization, DB) is unavailable and no partial
result can be produced. Enrichment failures never reach here.

---

## GET /health

```json
{ "status": "healthy" }
```

---

## Field enumerations

- `status`: `ok` | `no_movie_in_message` | `movie_not_found` | `insufficient_data`
- `sentiment.label`: `positive` | `neutral` | `negative`
- `aspect`: `plot` | `acting` | `visuals` | `sound` | `pacing`
- `audio_format`: `mp3` | null
