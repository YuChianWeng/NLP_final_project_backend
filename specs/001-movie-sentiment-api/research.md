# Phase 0 Research: Conversational Movie Review Sentiment & Narration Service

**Feature**: `001-movie-sentiment-api` | **Date**: 2026-05-26

This document resolves the technical unknowns for the pipeline. The user fixed the
high-level stack (FastAPI, Azure for sentiment + summarization, an LLM for refinement,
text-to-speech). The decisions below pin down the remaining choices.

---

## D1. Movie title extraction from conversational text

- **Decision**: Use the LLM (Azure OpenAI chat completion) to extract the movie title
  from the free-form message, returning a single normalized title string (or an explicit
  "none" sentinel when no movie is mentioned). Apply a lightweight bracket/quote heuristic
  (《...》, 「...」, "...") as a fast pre-pass before falling back to the LLM.
- **Rationale**: Conversational Traditional Chinese ("幫我查看看全面啟動") has no reliable
  delimiter; rule-only extraction is brittle. The project already depends on an LLM, so
  reusing it avoids adding an NER model. The heuristic pre-pass saves an LLM call for the
  common bracketed case.
- **Alternatives considered**:
  - Pure regex/keyword rules — rejected: too fragile for arbitrary phrasing.
  - Dedicated NER model (e.g., spaCy/transformers) — rejected: extra dependency and
    training/data burden for a class project; movie titles are open-vocabulary.

## D2. Aspect-level sentiment strategy (5 fixed aspects)

- **Decision**: Reviews are stored already tagged with one of the five canonical aspects
  (劇情 / 演技 / 視覺·特效 / 音效·配樂 / 節奏). For per-aspect sentiment, **group reviews by
  their stored aspect tag and run Azure sentiment analysis once per group**; compute the
  overall sentiment by running Azure sentiment over all of the movie's reviews.
- **Rationale**: Azure's Opinion Mining auto-extracts aspects from text and will not align
  to a fixed 5-aspect taxonomy. Grouping by the stored tag guarantees deterministic,
  complete coverage of exactly the five aspects the contract promises (FR-014), and is
  simpler to test.
- **Alternatives considered**:
  - Azure Opinion Mining (aspect-based sentiment) — rejected: detected targets are
    free-form and would need fuzzy mapping back to our 5 aspects.
  - One sentiment call per individual review then average per aspect — viable, but more
    API calls; batching per aspect group is cheaper and within Azure's document limits.

## D3. Sentiment aggregation → label + confidence

- **Decision**: For a group of reviews, send them as a batch to Azure sentiment, then
  aggregate to a single `{label, confidence}` by: majority vote on the per-document label;
  confidence = mean of the winning label's confidence scores. Same method for overall.
- **Rationale**: Azure returns per-document positive/neutral/negative plus confidence
  scores per class. Majority vote + mean confidence is a transparent, testable aggregation
  matching the contract (label + 0–1 confidence).
- **Alternatives considered**: Weighted average of class scores then argmax — slightly more
  nuanced but harder to explain/test; deferred as a possible refinement.

## D4. Review summarization

- **Decision**: Use **Azure AI Language Document Summarization (abstractive)** over the
  concatenated review texts to produce the raw summary, then pass that raw summary to the
  LLM (D5) for refinement.
- **Rationale**: Matches the user's request ("call azure ... summarize"). Abstractive gives
  more natural prose than extractive for a spoken narration use case.
- **Alternatives considered**: Extractive summarization — rejected: choppier output, worse
  for TTS. LLM-only summarization (skip Azure) — rejected: user explicitly wants Azure for
  the summary step, with the LLM as a separate polish stage.

## D5. LLM summary refinement

- **Decision**: Use Azure OpenAI chat completion with a system prompt instructing it to
  rewrite the Azure summary into fluent, natural Traditional Chinese suitable for narration,
  preserving facts and not inventing details. Fixed low temperature for stability.
- **Rationale**: Separates "what to say" (Azure summary) from "how it reads" (LLM polish),
  exactly as the spec sequences it. Low temperature keeps output testable.
- **Alternatives considered**: A non-Azure LLM provider — viable but keeping everything in
  Azure simplifies credentials/billing for the team.

## D6. Text-to-speech

- **Decision**: Use **Azure AI Speech** TTS with a Traditional-Chinese neural voice
  (e.g., `zh-TW-HsiaoChenNeural`), output **MP3**.
- **Rationale**: Output language is fixed to Traditional Chinese (FR-019); Azure Speech has
  high-quality zh-TW neural voices and integrates with the existing Azure footprint.
- **Alternatives considered**: gTTS/pyttsx3 — rejected: lower quality, less consistent with
  the Azure-centric stack the user requested.

## D7. Audio delivery format

- **Decision**: Return the audio **base64-encoded inline** in the single JSON response,
  alongside `audio_format: "mp3"`. The response is one self-contained bundle.
- **Rationale**: The spec requires audio + text + scores delivered **together** in one
  response (FR-018). Base64 inline is the simplest way to satisfy "together" without a
  second round trip or static-file hosting.
- **Alternatives considered**: Return a URL to a stored audio file — cleaner for large
  payloads but requires file hosting/cleanup; deferred as a future optimization if payload
  size becomes a problem.

## D8. Database technology

- **Decision**: **SQLite** accessed via **SQLAlchemy ORM**, with a seed script that loads
  sample movies/reviews. Schema is migration-friendly so it can swap to PostgreSQL later by
  changing only the connection URL.
- **Rationale**: The user wants a real, re-buildable database system (FR-009) but starting
  from a mock/seeded dataset (FR-008). SQLite needs zero infra so all three contributors can
  run the full stack locally; SQLAlchemy keeps the door open to PostgreSQL.
- **Alternatives considered**: In-memory dict/JSON file — rejected: not a real DB system
  (violates FR-009). PostgreSQL from day one — rejected: infra overhead unnecessary for a
  seeded class-project dataset.

## D9. Graceful degradation on external failures

- **Decision**: The orchestration pipeline wraps each external stage. Sentiment, summary,
  rating are core; refinement and TTS are enrichment. If refinement fails, return the raw
  Azure summary. If TTS fails, return text + scores with `audio = null`. A `warnings[]`
  / per-field `status` block tells the frontend which enrichment was skipped (FR-018, FR-021).
- **Rationale**: Spec requires never returning an empty failure when partial results exist
  (SC-006).
- **Alternatives considered**: Fail the whole request on any error — rejected: violates
  FR-018/FR-021/SC-006.

## D10. API surface & framework

- **Decision**: Single **FastAPI** `POST /api/v1/movie-insight` endpoint taking
  `{ "message": "<text>" }` and returning the result bundle. Pydantic models define the
  request/response contract. A separate `GET /health` for liveness.
- **Rationale**: One message in, one bundle out (FR-020). FastAPI + Pydantic gives an
  enforceable, documented contract (auto OpenAPI) the three contributors code against.
- **Alternatives considered**: Multiple granular endpoints per stage — rejected for the
  public contract (frontend wants one call), though internal service functions remain
  separately testable.

---

## Resolved Technical Context

| Field | Value |
|-------|-------|
| Language/Version | Python 3.11+ |
| Primary Dependencies | FastAPI, Uvicorn, Pydantic, SQLAlchemy, azure-ai-textanalytics, azure-cognitiveservices-speech (or Speech SDK), openai (Azure OpenAI), python-dotenv |
| Storage | SQLite (via SQLAlchemy); PostgreSQL-swappable |
| Testing | pytest + httpx (FastAPI TestClient) |
| Target Platform | Linux server |
| Project Type | Web service (backend API); frontend is external/out of scope |
| Performance Goals | Full bundle within 10s for 95% of requests (SC-001) — latency dominated by external Azure calls |
| Constraints | Graceful degradation when Azure stages fail; Traditional-Chinese output |
| Scale/Scope | Small seeded dataset (class-project scale); single-request interaction |

**All NEEDS CLARIFICATION resolved.** No open unknowns remain for Phase 1.
