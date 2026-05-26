# Phase 1 Data Model: Conversational Movie Review Sentiment & Narration Service

**Feature**: `001-movie-sentiment-api` | **Date**: 2026-05-26

Two layers are modeled:
1. **Persistent entities** (database, owned by Stream A) — what is stored.
2. **Transient analysis objects** (computed per request) — what flows through the pipeline.

---

## 1. Persistent Entities (SQLite via SQLAlchemy)

### Aspect (enumeration, not a table)

Fixed set of five canonical aspects. Stored as a string code on each review.

| Code | Display (zh-TW) |
|------|-----------------|
| `plot` | 劇情 |
| `acting` | 演技 |
| `visuals` | 視覺/特效 |
| `sound` | 音效/配樂 |
| `pacing` | 節奏 |

> Validation: a review's `aspect` MUST be one of these five codes.

### Movie

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, autoincrement |
| `canonical_title` | str | NOT NULL, indexed |
| `normalized_title` | str | NOT NULL, indexed — lowercased, whitespace/punctuation-stripped form of `canonical_title` (used for matching, FR-006) |
| `created_at` | datetime | default now |

Relationships: `Movie` 1—* `Review`; `Movie` 1—* `MovieAlias`.

### MovieAlias

Alternate titles (English name, abbreviations, common variants) to support normalized
matching against more than the canonical title (FR-006).

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK |
| `movie_id` | int | FK → Movie.id, NOT NULL |
| `alias_title` | str | NOT NULL |
| `normalized_alias` | str | NOT NULL, indexed |

### Review

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK |
| `movie_id` | int | FK → Movie.id, NOT NULL |
| `aspect` | str | NOT NULL, one of the 5 Aspect codes (FR-005) |
| `rating` | float | NOT NULL, 1.0–5.0 (FR-005) |
| `text` | str | NOT NULL — the review body used for sentiment + summary |
| `created_at` | datetime | default now |

**Validation rules**
- `rating` in [1.0, 5.0].
- `aspect` in the five canonical codes.
- A movie may have zero reviews → triggers the "insufficient data" path (FR-015).

**Matching rule (FR-006)**: `normalize(extracted_title)` is compared against
`Movie.normalized_title` and `MovieAlias.normalized_alias`. On multiple hits, prefer a
canonical-title match over an alias match (Edge Cases). `normalize()` = casefold + strip
whitespace + remove punctuation/brackets.

---

## 2. Transient Analysis Objects (per request, Pydantic)

### ConversationRequest (inbound)

| Field | Type | Notes |
|-------|------|-------|
| `message` | str | Free-form user text (FR-001), non-empty |

### SentimentResult (reused for overall and each aspect)

| Field | Type | Notes |
|-------|------|-------|
| `label` | enum(`positive`,`neutral`,`negative`) | FR-011/FR-014 |
| `confidence` | float | 0.0–1.0 |

### AspectSentiment

| Field | Type | Notes |
|-------|------|-------|
| `aspect` | str | one of 5 codes |
| `aspect_display` | str | zh-TW label |
| `sentiment` | SentimentResult \| null | null if that aspect has no reviews |
| `review_count` | int | reviews contributing to this aspect |

### AnalysisResult (internal, produced by the analysis stream)

| Field | Type | Notes |
|-------|------|-------|
| `movie_rating` | float | avg of stored 1–5 ratings, 1 decimal (FR-013) |
| `overall_sentiment` | SentimentResult | FR-011 |
| `aspect_sentiments` | AspectSentiment[5] | one per canonical aspect (FR-014) |
| `raw_summary` | str | Azure summarization output (FR-012) |
| `refined_summary` | str | LLM-polished text (FR-016); falls back to raw_summary on failure |

### ResultBundle (outbound response, FR-018)

| Field | Type | Notes |
|-------|------|-------|
| `status` | enum(`ok`,`movie_not_found`,`no_movie_in_message`,`insufficient_data`) | top-level outcome |
| `matched_movie` | object\|null | `{ id, canonical_title }` of the resolved movie |
| `movie_rating` | float\|null | 1–5, one decimal |
| `overall_sentiment` | SentimentResult\|null | label + confidence |
| `aspect_sentiments` | AspectSentiment[]\|null | per-aspect breakdown |
| `summary_text` | str\|null | the refined summary (or raw if refinement skipped) |
| `audio_base64` | str\|null | MP3 bytes, base64; null if TTS skipped |
| `audio_format` | str\|null | `"mp3"` when audio present |
| `warnings` | string[] | which enrichment steps were skipped/degraded (FR-018/FR-021) |

---

## State / Flow

```
message
  → [extract title]          (none → status=no_movie_in_message)
  → [normalized DB lookup]   (miss → status=movie_not_found)
  → reviews                  (empty → status=insufficient_data)
  → [Azure sentiment: overall + per aspect group]
  → [Azure summarize] → raw_summary
  → [avg ratings] → movie_rating
  → [LLM refine] → refined_summary   (fail → use raw_summary, +warning)
  → [Azure TTS] → audio_base64        (fail → null, +warning)
  → ResultBundle (status=ok)
```

## Ownership map (3-person split)

- **Stream A**: Movie, MovieAlias, Review, Aspect enum, `normalize()`, seed data, lookup.
- **Stream B**: SentimentResult, AspectSentiment, AnalysisResult (sentiment + summary + rating).
- **Stream C**: ResultBundle assembly, refined_summary, audio_base64 (refine + TTS + API).
