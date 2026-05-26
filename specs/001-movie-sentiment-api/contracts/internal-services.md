# Internal Service Contracts (3-person handoff)

**Feature**: `001-movie-sentiment-api` | **Date**: 2026-05-26

These are the function-level contracts between the three work streams. If everyone codes to
these signatures, the three streams can be built and unit-tested **independently** with
fake inputs and only integrated at the end (SC-007). Types reference `data-model.md`.

---

## Stream A — Extraction + Database (User Story 1)

```python
# services/extraction.py
def extract_movie_title(message: str) -> str | None:
    """Return the movie title found in the message, or None if no movie is mentioned."""

# services/repository.py
def find_movie(extracted_title: str) -> Movie | None:
    """Normalized lookup against canonical_title + aliases (FR-006).
       Prefer canonical-title hit over alias hit on ties. None if no match."""

def get_reviews(movie_id: int) -> list[Review]:
    """All reviews for a movie; may be empty (→ insufficient_data)."""

# db/seed.py
def seed() -> None:
    """Populate the DB with sample movies/reviews so the pipeline runs end-to-end."""
```

**A's test doubles**: a small fixture DB. A can ship without B/C by asserting
`find_movie` + `get_reviews` return correct rows for seeded titles and `None` for misses.

---

## Stream B — Analysis (User Story 2)

```python
# services/sentiment.py
def analyze_overall(review_texts: list[str]) -> SentimentResult:
    """Azure sentiment over all reviews → aggregated label + confidence (D3)."""

def analyze_by_aspect(reviews: list[Review]) -> list[AspectSentiment]:
    """Group reviews by stored aspect, run Azure sentiment per group,
       return one AspectSentiment per canonical aspect (sentiment=None if no reviews)."""

# services/summarizer.py
def summarize(review_texts: list[str]) -> str:
    """Azure abstractive summarization → raw summary (FR-012)."""

# services/scoring.py
def average_rating(reviews: list[Review]) -> float:
    """Mean of 1–5 ratings, rounded to 1 decimal (FR-013)."""
```

**B's test doubles**: hand-written `Review` objects + a mocked Azure client. B can ship
without A/C by feeding fixed review lists and asserting the analysis outputs. Live Azure
calls are exercised in integration tests behind an env-gated marker.

---

## Stream C — Refinement + TTS + Assembly (User Story 3)

```python
# services/refiner.py
def refine_summary(raw_summary: str) -> str:
    """LLM polish into natural zh-TW; on failure raise RefinementUnavailable."""

# services/tts.py
def synthesize(text: str) -> bytes:
    """Azure TTS → MP3 bytes (zh-TW voice); on failure raise TtsUnavailable."""

# services/pipeline.py
def run_pipeline(message: str) -> ResultBundle:
    """Orchestrate A → B → C, apply status branching and graceful degradation (D9),
       return the final ResultBundle."""

# api/routes.py
@router.post("/api/v1/movie-insight")
def movie_insight(req: ConversationRequest) -> ResultBundle: ...
```

**C's test doubles**: a sample raw summary string + mocked LLM/TTS clients. C can ship
without A/B by asserting that `run_pipeline` assembles the bundle correctly and that
`refine`/`tts` failures degrade to `warnings` + null audio rather than erroring.

---

## Shared status branching (owned by pipeline, agreed by all)

| Condition | Resulting `status` |
|-----------|--------------------|
| `extract_movie_title` returns None | `no_movie_in_message` |
| `find_movie` returns None | `movie_not_found` |
| `get_reviews` returns empty | `insufficient_data` |
| all stages succeed | `ok` |
| refine/tts raise their *Unavailable* errors | `ok` + `warnings[]`, affected fields null |

**Integration order**: A and B mock each other via the types above; C integrates last by
calling real A + B. No stream blocks another as long as the signatures here hold.
