---
description: "Task list for Conversational Movie Review Sentiment & Narration Service"
---

# Tasks: Conversational Movie Review Sentiment & Narration Service

**Input**: Design documents from `/specs/001-movie-sentiment-api/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks ARE included. The spec makes per-stream independent testability a
core requirement (SC-007) and `contracts/internal-services.md` specifies mocked unit tests
per stream so the three contributors can work in parallel. Azure-dependent tests are mocked
in unit tests; live Azure calls are isolated in env-gated integration tests.

**Organization**: Tasks are grouped by user story (US1/US2/US3), which map 1:1 to the three
work streams (A/B/C).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 = Stream A, US2 = Stream B, US3 = Stream C

## Path Conventions

Single backend project rooted at `backend/` (per plan.md Structure Decision).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure (`backend/app/{api,schemas,models,db,services,lib}`, `backend/tests/{unit,contract,integration}`) per plan.md
- [ ] T002 Create `backend/requirements.txt` with FastAPI, uvicorn, pydantic, SQLAlchemy, azure-ai-textanalytics, azure-cognitiveservices-speech, openai, python-dotenv, pytest, httpx
- [ ] T003 [P] Create `backend/.env.example` with Azure Language/OpenAI/Speech keys, `DATABASE_URL`, `TTS_VOICE` (per quickstart.md)
- [ ] T004 [P] Configure tooling: `backend/pyproject.toml` (ruff/black) and `backend/pytest.ini` with `RUN_AZURE` marker

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement settings/config loader (Azure keys, DB URL, TTS voice) in `backend/app/config.py`
- [ ] T006 Implement SQLAlchemy engine, session factory, and declarative `Base` in `backend/app/db/database.py`
- [ ] T007 [P] Define the five canonical Aspect codes + zh-TW display map in `backend/app/lib/aspects.py`
- [ ] T008 [P] Define shared sentiment types (label enum `positive`/`neutral`/`negative` + `SentimentResult` model) in `backend/app/schemas/common.py`
- [ ] T009 Create FastAPI app skeleton with `GET /health` in `backend/app/main.py`

**Checkpoint**: Foundation ready — the three user stories can now proceed in parallel.

---

## Phase 3: User Story 1 - Identify a movie from a conversational request (Priority: P1) 🎯 MVP

**Goal**: Given a conversational message, extract the movie title, look it up in the seeded
database via normalized matching, and return the matched movie with its reviews/aspect ratings.

**Independent Test**: Send messages naming seeded movies → correct movie + reviews returned;
send a no-movie or unknown-movie message → defined response. (Stream A; mocks not required.)

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test normalized lookup (canonical + alias hits, ties, misses) in `backend/tests/unit/test_repository.py`
- [ ] T011 [P] [US1] Unit test title extraction (bracketed heuristic + mocked LLM fallback + no-movie case) in `backend/tests/unit/test_extraction.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `Movie`, `MovieAlias`, `Review` SQLAlchemy models (with `normalized_title`/`normalized_alias`, aspect + 1–5 rating constraints) in `backend/app/models/movie.py`
- [ ] T013 [P] [US1] Implement `normalize()` (casefold + strip whitespace/punctuation/brackets) in `backend/app/lib/normalize.py`
- [ ] T014 [US1] Implement `find_movie()` (normalized match vs canonical + aliases, prefer canonical on ties) and `get_reviews()` in `backend/app/services/repository.py` (depends on T012, T013)
- [ ] T015 [US1] Implement `extract_movie_title()` (heuristic pre-pass → Azure OpenAI fallback, returns title or None) in `backend/app/services/extraction.py` (depends on T005)
- [ ] T016 [US1] Implement DB seed loading ≥3 sample movies with aspect-tagged 1–5 reviews + aliases (auto-populating normalized fields) in `backend/app/db/seed.py` (depends on T012)

**Checkpoint**: US1 fully functional — extraction + DB lookup testable end-to-end on its own.

---

## Phase 4: User Story 2 - Analyze reviews into ratings, sentiment, and a summary (Priority: P2)

**Goal**: Given a movie's reviews, produce an averaged 1–5 movie rating, overall + per-aspect
sentiment (label + confidence), and a raw review summary.

**Independent Test**: Feed a fixed list of `Review` objects (bypassing extraction) with a
mocked Azure client → assert rating, overall sentiment, five aspect sentiments, and a summary.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test `average_rating()` (1-decimal rounding, empty list) in `backend/tests/unit/test_scoring.py`
- [ ] T018 [P] [US2] Unit test sentiment aggregation — overall + per-aspect grouping, majority-vote label + mean confidence, empty-aspect → null (mocked Azure) in `backend/tests/unit/test_sentiment.py`
- [ ] T019 [P] [US2] Unit test `summarize()` with mocked Azure summarization client in `backend/tests/unit/test_summarizer.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement analysis schemas (`AspectSentiment`, `AnalysisResult`) in `backend/app/schemas/analysis.py` (depends on T008)
- [ ] T021 [P] [US2] Implement `average_rating()` (mean of 1–5 ratings, round to 1 decimal) in `backend/app/services/scoring.py`
- [ ] T022 [US2] Implement Azure sentiment client `analyze_overall()` + `analyze_by_aspect()` (group reviews by stored aspect, aggregate label+confidence) in `backend/app/services/sentiment.py` (depends on T005, T007, T008)
- [ ] T023 [US2] Implement Azure abstractive `summarize()` over concatenated review texts in `backend/app/services/summarizer.py` (depends on T005)

**Checkpoint**: US2 produces rating + sentiment + summary from fixed review input, independently.

---

## Phase 5: User Story 3 - Deliver a polished, spoken result bundle (Priority: P3)

**Goal**: Refine the raw summary via LLM into natural zh-TW, synthesize MP3 audio, and assemble
the single `ResultBundle` (rating, sentiment, refined text, audio) with graceful degradation.

**Independent Test**: Provide a sample raw summary + scores with mocked LLM/TTS → assert refined
text returned, audio produced, and that LLM/TTS failures degrade to `warnings[]` + null audio
rather than erroring. Contract test asserts response schema.

### Tests for User Story 3

- [ ] T024 [P] [US3] Contract test for `POST /api/v1/movie-insight` (request/response shape, all `status` outcomes) in `backend/tests/contract/test_movie_insight_contract.py`
- [ ] T025 [P] [US3] Unit test `run_pipeline` status branching (no_movie / not_found / insufficient_data / ok) with all stages mocked in `backend/tests/unit/test_pipeline.py`
- [ ] T026 [P] [US3] Unit test refiner fallback (→ raw summary + warning) and TTS failure (→ null audio + warning) in `backend/tests/unit/test_refiner_tts.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `ConversationRequest` + `ResultBundle` (incl. `status`, `warnings`, `audio_base64`/`audio_format`) schemas in `backend/app/schemas/bundle.py` (depends on T008, T020)
- [ ] T028 [P] [US3] Implement `refine_summary()` (Azure OpenAI, zh-TW, low temp; raise `RefinementUnavailable` on failure) in `backend/app/services/refiner.py` (depends on T005)
- [ ] T029 [P] [US3] Implement `synthesize()` (Azure TTS zh-TW → MP3 bytes; raise `TtsUnavailable` on failure) in `backend/app/services/tts.py` (depends on T005)
- [ ] T030 [US3] Implement `run_pipeline()` orchestration (A→B→C, status branching, base64 audio, graceful degradation per D9) in `backend/app/services/pipeline.py` (depends on T014, T015, T021, T022, T023, T027, T028, T029)
- [ ] T031 [US3] Implement `POST /api/v1/movie-insight` route + 400 on empty message, mounted in `backend/app/api/routes.py` and wired into `backend/app/main.py` (depends on T030)

**Checkpoint**: All three stories integrate — full pipeline returns the bundle end-to-end.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T032 [P] Add env-gated (`RUN_AZURE=1`) live integration test of the full pipeline in `backend/tests/integration/test_pipeline_live.py`
- [ ] T033 [P] Add request/error logging + exception handler (502/503 only for core-stage failures) in `backend/app/main.py`
- [ ] T034 Run `quickstart.md` smoke test + all four edge-case checks; fix any gaps
- [ ] T035 Performance sanity check against SC-001 (full bundle < 10s for 95% of requests)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational. US1/US2 are fully independent and
  can run in parallel. US3's *implementation* of `run_pipeline` (T030) integrates US1+US2
  services, but US3's tests + schemas + refiner/tts (T024–T029) are independent and can start
  immediately after Foundational.
- **Polish (Phase 6)**: Depends on US1–US3 complete.

### User Story Dependencies

- **US1 (P1, Stream A)**: After Foundational. No dependency on other stories. → MVP.
- **US2 (P2, Stream B)**: After Foundational. Independent (uses fixed `Review` input).
- **US3 (P3, Stream C)**: After Foundational. Builds the final bundle; `run_pipeline` (T030)
  needs US1+US2 service functions, but all other US3 tasks are independent (mock the inputs).

### Within Each User Story

- Tests written first and expected to FAIL before implementation.
- Models/schemas before services; services before endpoints; core before integration.

### Parallel Opportunities

- Setup: T003, T004 in parallel.
- Foundational: T007, T008 in parallel.
- Once Foundational done, the three streams run concurrently:
  - **Stream A**: T010–T016
  - **Stream B**: T017–T023
  - **Stream C**: T024–T029 (then T030–T031 once A+B services land)
- Within a story, all [P] tasks (separate files) run in parallel.

---

## Parallel Example: kick off all three streams after Phase 2

```bash
# Stream A (Developer A):
Task: "T010 Unit test repository in backend/tests/unit/test_repository.py"
Task: "T012 Movie/MovieAlias/Review models in backend/app/models/movie.py"
Task: "T013 normalize() in backend/app/lib/normalize.py"

# Stream B (Developer B):
Task: "T018 Sentiment aggregation unit test in backend/tests/unit/test_sentiment.py"
Task: "T020 Analysis schemas in backend/app/schemas/analysis.py"
Task: "T021 average_rating in backend/app/services/scoring.py"

# Stream C (Developer C):
Task: "T024 Contract test in backend/tests/contract/test_movie_insight_contract.py"
Task: "T027 Request/ResultBundle schemas in backend/app/schemas/bundle.py"
Task: "T028 refine_summary in backend/app/services/refiner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 → **STOP & VALIDATE**: send a
   conversational message, confirm correct movie + reviews returned (and not-found/no-movie paths).

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → conversational lookup works (MVP, demoable).
3. US2 → add rating + sentiment + summary.
4. US3 → add LLM polish + audio + assembled bundle (full feature).

### Parallel Team Strategy (3 people)

1. Whole team finishes Setup + Foundational together (define `config`, `database`, shared
   enums/schemas — the contracts everyone depends on).
2. Then split per `contracts/internal-services.md`: A → US1, B → US2, C → US3.
3. C integrates last via `run_pipeline` once A+B service functions are merged.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- [US#] maps each task to its stream for traceability.
- Mock Azure/LLM/TTS in unit tests; run real Azure only in `RUN_AZURE=1` integration tests.
- Agree on the `contracts/internal-services.md` signatures BEFORE splitting — that is what
  keeps the three streams unblocked.
- Commit after each task or logical group; validate at each checkpoint.
