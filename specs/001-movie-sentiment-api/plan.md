# Implementation Plan: Conversational Movie Review Sentiment & Narration Service

**Branch**: `001-movie-sentiment-api` | **Date**: 2026-05-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-movie-sentiment-api/spec.md`

## Summary

A FastAPI backend that takes a single conversational message (e.g., "幫我查看看全面啟動"),
extracts the movie title, looks it up in a seeded database of aspect-tagged reviews, then
runs an analysis pipeline: Azure sentiment (overall + per the five canonical aspects),
Azure abstractive summarization, and an averaged 1–5 movie rating. The raw summary is
polished by an LLM into natural Traditional Chinese, converted to MP3 via Azure TTS, and
everything (rating, sentiment, refined text, audio) is returned in one self-contained
response bundle. Enrichment failures (LLM/TTS) degrade gracefully instead of failing the
request. Work is split into three independently testable streams for a 3-person team.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Uvicorn, Pydantic, SQLAlchemy, azure-ai-textanalytics (AI Language: sentiment + summarization), Azure OpenAI via `openai` SDK (extraction + refinement), Azure Speech SDK (TTS), python-dotenv  
**Storage**: SQLite via SQLAlchemy (PostgreSQL-swappable by connection URL)  
**Testing**: pytest + FastAPI TestClient (httpx); Azure-dependent tests env-gated (`RUN_AZURE=1`)  
**Target Platform**: Linux server  
**Project Type**: Web service (backend API); frontend is external and out of scope  
**Performance Goals**: Complete bundle within 10s for 95% of requests (SC-001); latency dominated by external Azure calls  
**Constraints**: Traditional-Chinese output (FR-019); graceful degradation when enrichment stages fail (FR-018/FR-021/SC-006)  
**Scale/Scope**: Small seeded dataset (class-project scale); single-request interaction, no multi-turn state

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`.specify/memory/constitution.md`) is still the unratified
template (no concrete principles defined). There are therefore **no enforceable gates**.
The plan voluntarily follows common-sense defaults:

- **Separation / testability**: each pipeline stage is an independent service function with
  an explicit contract (see `contracts/internal-services.md`) — enables 3-person parallelism.
- **Test-first friendly**: every stream has fully-mocked unit tests; Azure integration tests
  are isolated behind an env gate.
- **Simplicity**: single backend project, single public endpoint, SQLite (no infra).

No violations to justify → Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-movie-sentiment-api/
├── plan.md              # This file
├── spec.md              # Feature specification (with clarifications)
├── research.md          # Phase 0 — technical decisions (D1–D10)
├── data-model.md        # Phase 1 — persistent + transient models
├── quickstart.md        # Phase 1 — setup, run, smoke test
├── contracts/
│   ├── http-api.md          # public POST /api/v1/movie-insight contract
│   └── internal-services.md # function contracts for the 3-stream handoff
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # Phase 2 — created by /speckit-tasks (not here)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                 # FastAPI app, mounts router, /health
│   ├── config.py               # env settings (Azure keys, DB URL, TTS voice)
│   ├── api/
│   │   └── routes.py           # POST /api/v1/movie-insight  [Stream C]
│   ├── schemas/
│   │   └── bundle.py           # Pydantic: ConversationRequest, ResultBundle, etc.
│   ├── models/
│   │   └── movie.py            # SQLAlchemy: Movie, MovieAlias, Review  [Stream A]
│   ├── db/
│   │   ├── database.py         # engine/session  [Stream A]
│   │   └── seed.py             # sample movies/reviews  [Stream A]
│   ├── services/
│   │   ├── extraction.py       # title extraction (heuristic + LLM)  [Stream A]
│   │   ├── repository.py       # normalized lookup, get_reviews  [Stream A]
│   │   ├── sentiment.py        # Azure sentiment: overall + per aspect  [Stream B]
│   │   ├── summarizer.py       # Azure abstractive summary  [Stream B]
│   │   ├── scoring.py          # average 1–5 rating  [Stream B]
│   │   ├── refiner.py          # LLM polish  [Stream C]
│   │   ├── tts.py              # Azure TTS → mp3 bytes  [Stream C]
│   │   └── pipeline.py         # orchestration + status branching + degradation  [Stream C]
│   └── lib/
│       └── normalize.py        # normalize() title helper (shared, owned by A)
├── tests/
│   ├── unit/                   # per-stream, mocked
│   ├── contract/               # request/response schema conformance
│   └── integration/            # live Azure (RUN_AZURE=1)
├── requirements.txt
└── .env.example
```

**Structure Decision**: Single backend web-service project under `backend/`. The directory
layout deliberately mirrors the three work streams (A = models/db/extraction/repository,
B = sentiment/summarizer/scoring, C = refiner/tts/pipeline/api), each with its own unit
test file, so the three contributors can develop in parallel against the contracts.

## Phase 0 — Research

Complete. See [research.md](./research.md). All technical unknowns resolved (D1–D10):
LLM title extraction, group-by-aspect sentiment strategy, label+confidence aggregation,
Azure abstractive summarization, LLM refinement, Azure zh-TW TTS, base64-inline audio,
SQLite+SQLAlchemy, graceful degradation, single FastAPI endpoint.

## Phase 1 — Design & Contracts

Complete. Artifacts:
- [data-model.md](./data-model.md) — persistent entities (Movie/MovieAlias/Review, 5-aspect enum) + transient pipeline objects.
- [contracts/http-api.md](./contracts/http-api.md) — public endpoint contract incl. status/degraded responses.
- [contracts/internal-services.md](./contracts/internal-services.md) — per-stream function signatures for parallel work.
- [quickstart.md](./quickstart.md) — setup, seed, run, smoke + edge-case tests.
- Agent context (`CLAUDE.md`) updated to point at this plan.

**Post-Design Constitution Re-check**: still no enforceable gates (template constitution);
design honors the voluntary defaults above. No violations.

## Complexity Tracking

> No constitution violations to justify — section intentionally empty.

## Phase 2 — Next step

Run `/speckit-tasks` to generate the dependency-ordered `tasks.md`. Tasks should be grouped
by the three streams (A/B/C) and ordered: shared models/contracts → per-stream services +
unit tests → pipeline integration → contract/integration tests → quickstart validation.
