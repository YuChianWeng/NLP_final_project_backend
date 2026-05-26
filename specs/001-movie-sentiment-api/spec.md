# Feature Specification: Conversational Movie Review Sentiment & Narration Service

**Feature Branch**: `001-movie-sentiment-api`  
**Created**: 2026-05-26  
**Status**: Draft  
**Input**: User description: "前端傳一個對話（例如「幫我查看看某某某電影」），後端提取電影名稱、在資料庫查詢該電影的多面向評論與評分，呼叫情緒分析與摘要產生電影評分、情緒評分、評論摘要，再請 LLM 修飾摘要，最後用文字轉語音把音檔、文字與評分一起回傳給前端。需建置資料庫系統，三人分工。"

## Clarifications

### Session 2026-05-26

- Q: Which fixed set of review aspects should the system store and report per-aspect sentiment for? → A: Fixed 5 aspects — 劇情 (plot), 演技 (acting), 視覺/特效 (visuals), 音效/配樂 (sound), 節奏 (pacing).
- Q: What numeric scale do stored review ratings and the averaged movie rating use? → A: 1–5 scale; movie rating is the average rounded to one decimal (e.g., 4.3).
- Q: How is the sentiment score represented in the response? → A: A label (positive/neutral/negative) plus a 0–1 confidence score, provided both overall and per aspect.
- Q: What rule matches the extracted title to a stored movie? → A: Normalized match — case/whitespace/punctuation-insensitive — against both canonical and alternate titles.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify a movie from a conversational request (Priority: P1)

A frontend user types a natural-language message such as "幫我查看看《全面啟動》這部電影". The backend understands the message, extracts the movie title, looks it up in the review database, and returns the matched movie together with its stored multi-aspect reviews and ratings.

**Why this priority**: Without reliable extraction and lookup, no downstream analysis is possible. This is the entry point of the entire pipeline and the foundation the other stories build on. It is also the natural ownership boundary for one team member (conversation parsing + database).

**Independent Test**: Send several conversational messages naming movies that exist in the seeded database and confirm the correct movie record (with its reviews and aspect ratings) is returned; send a message that names no movie or an unknown movie and confirm a clear, defined response.

**Acceptance Scenarios**:

1. **Given** the database contains a movie titled "全面啟動", **When** the user sends "幫我查看看全面啟動", **Then** the system extracts "全面啟動" and returns that movie's stored reviews and aspect ratings.
2. **Given** a conversational message that contains no recognizable movie title, **When** the message is submitted, **Then** the system responds with a clear request for the user to name a movie (no analysis is attempted).
3. **Given** a movie title that is not present in the database, **When** the message is submitted, **Then** the system returns a defined "movie not found" response.

---

### User Story 2 - Analyze reviews into ratings, sentiment, and a summary (Priority: P2)

Given a matched movie and its stored reviews, the system produces three analytical outputs: an overall movie rating, an overall sentiment score, and a concise summary of the reviews.

**Why this priority**: This is the core analytical value of the product. It depends on Story 1 providing the review data, but can be developed and tested independently using stored reviews as fixed input. This is the natural ownership boundary for a second team member (sentiment analysis + summarization + scoring).

**Independent Test**: Feed a fixed set of stored reviews (bypassing extraction) into the analysis step and confirm it returns a numeric movie rating, a sentiment score, and a text summary that reflects the review content.

**Acceptance Scenarios**:

1. **Given** a movie with multiple reviews, **When** analysis runs, **Then** the system returns an overall movie rating derived from the review data.
2. **Given** the same set of reviews, **When** analysis runs, **Then** the system returns an overall sentiment score reflecting the positive/negative balance of the reviews.
3. **Given** the same set of reviews, **When** analysis runs, **Then** the system returns a review summary that captures the main points across reviews.
4. **Given** a movie that exists but has zero reviews, **When** analysis runs, **Then** the system returns a defined response indicating insufficient data instead of failing.

---

### User Story 3 - Deliver a polished, spoken result bundle (Priority: P3)

The raw review summary is refined by a language model to read more naturally, then converted to spoken audio. The system returns a single bundle to the frontend containing the movie rating, sentiment score, refined summary text, and the audio.

**Why this priority**: This delivers the final user-facing experience and presentation polish. It depends on Story 2's outputs but can be developed and tested independently by feeding it a sample summary. This is the natural ownership boundary for a third team member (LLM refinement + text-to-speech + response assembly).

**Independent Test**: Provide a sample raw summary and scores, confirm the refined text is returned, confirm playable audio is produced from the refined text, and confirm all four elements (rating, sentiment score, refined text, audio) are returned together in one response.

**Acceptance Scenarios**:

1. **Given** a raw review summary, **When** refinement runs, **Then** the system returns a refined summary that preserves the meaning while improving readability.
2. **Given** a refined summary, **When** audio generation runs, **Then** the system returns playable audio whose spoken content matches the refined summary.
3. **Given** all analysis outputs are ready, **When** the response is assembled, **Then** the frontend receives one response containing the movie rating, the sentiment score, the refined summary text, and the audio.

---

### Edge Cases

- The conversational message names multiple movies — system selects and analyzes the first/most-likely title and indicates which movie it answered for.
- The extracted title normalizes to several movies in the database — system selects a single best match (preferring a canonical-title hit over an alternate-title hit) and reports which movie was chosen.
- An external capability (sentiment analysis, summarization, language-model refinement, or text-to-speech) is temporarily unavailable — system returns a graceful, partial response rather than failing the whole request (see FR-018).
- The review text is very long or numerous — system still returns a result within the response-time target (see SC-001).
- The message is empty or whitespace only — system returns a clear prompt to provide a request.

## Requirements *(mandatory)*

### Functional Requirements

**Conversation handling & movie extraction**

- **FR-001**: System MUST accept a free-form conversational text message submitted by the frontend.
- **FR-002**: System MUST extract the intended movie title from the conversational message.
- **FR-003**: System MUST return a clear, defined response when no movie title can be identified in the message.

**Movie & review database**

- **FR-004**: System MUST provide a queryable database of movies, where each movie has a title and a set of associated reviews.
- **FR-005**: Each stored review MUST be associated with one or more of the five canonical review aspects — 劇情 (plot), 演技 (acting), 視覺/特效 (visuals), 音效/配樂 (sound), 節奏 (pacing) — and a numeric rating on a 1–5 scale.
- **FR-006**: System MUST look up a movie by its extracted title using normalized matching — case-, whitespace-, and punctuation-insensitive — against both the movie's canonical title and its alternate titles.
- **FR-007**: System MUST return a defined "movie not found" response when no stored movie matches the extracted title.
- **FR-008**: System MUST be seeded with sample movies and reviews so the full pipeline can be exercised before real data exists (a virtual/mock dataset is acceptable for the initial version).
- **FR-009**: The database MUST be a persistent, re-buildable system (schema + seed data) rather than values hard-coded inside request handling, so the team can grow the dataset over time.

**Analysis (rating, sentiment, summary)**

- **FR-010**: System MUST submit the matched movie's review texts to a sentiment analysis capability.
- **FR-011**: System MUST produce an overall sentiment result for the movie derived from its review texts, expressed as a label (positive / neutral / negative) together with a 0–1 confidence score.
- **FR-012**: System MUST produce a review summary generated from the movie's review texts.
- **FR-013**: System MUST produce an overall movie rating computed as the average of the stored 1–5 numeric review ratings for the matched movie, rounded to one decimal place (e.g., 4.3). The movie rating is kept distinct from the sentiment score.
- **FR-014**: System MUST report sentiment both overall and per aspect across the five canonical aspects (劇情, 演技, 視覺/特效, 音效/配樂, 節奏), where each aspect's sentiment is also expressed as a label (positive / neutral / negative) plus a 0–1 confidence score.
- **FR-015**: System MUST return a defined "insufficient data" response when a matched movie has no reviews, instead of failing.

**Refinement & delivery**

- **FR-016**: System MUST refine the generated review summary using a language model to improve readability and naturalness while preserving meaning.
- **FR-017**: System MUST convert the refined summary text into spoken audio.
- **FR-018**: System MUST return a single response bundle to the frontend containing: the movie rating, the sentiment score, the refined summary text, and the audio. If an optional enrichment step (refinement or audio) is unavailable, the system MUST still return the available results and indicate which parts are missing.
- **FR-019**: The spoken audio, summary text, and any displayed labels MUST be produced in Traditional Chinese.

**Cross-cutting**

- **FR-020**: System MUST expose the pipeline through a single request/response interaction so the frontend can send one message and receive one result bundle.
- **FR-021**: System MUST handle failures of external capabilities without crashing, returning a user-understandable error or partial result.

### Key Entities *(include if feature involves data)*

- **Movie**: A film that can be queried. Attributes: canonical title, optional alternate titles, and an aggregate movie rating. Has many Reviews.
- **Review**: A single critique of a movie. Attributes: review text, one or more associated Aspects, and a numeric rating. Belongs to one Movie.
- **Aspect (Dimension)**: One of the five canonical facets a review can address — 劇情 (plot), 演技 (acting), 視覺/特效 (visuals), 音效/配樂 (sound), 節奏 (pacing). Used to organize reviews and drive aspect-level sentiment reporting.
- **Analysis Result**: The computed output for a movie request. Attributes: overall movie rating (1–5, one decimal), overall sentiment (label + 0–1 confidence), per-aspect sentiment (label + 0–1 confidence for each of the five aspects), raw review summary, refined summary text, and generated audio.
- **Conversation Request**: The inbound message from the frontend. Attributes: raw user message text.
- **Result Bundle**: The outbound response to the frontend. Attributes: identified movie, movie rating, sentiment score, refined summary text, audio, and status indicators for any missing parts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a well-formed request naming a movie in the database, the user receives the complete result bundle (rating, sentiment score, summary text, and audio) within 10 seconds for 95% of requests.
- **SC-002**: For well-formed requests that name a movie present in the database, the system extracts and matches the correct movie at least 90% of the time.
- **SC-003**: For requests naming a movie not in the database (or naming no movie), the system returns the appropriate defined response 100% of the time without crashing.
- **SC-004**: The generated audio is playable and its spoken content matches the refined summary text in 100% of successful responses.
- **SC-005**: In reviewer comparison, the LLM-refined summary is judged as readable or more readable than the raw summary in at least 80% of sampled cases, with no loss of factual meaning.
- **SC-006**: When an external enrichment capability is unavailable, the system still returns the available results (never an empty failure) in 100% of such cases.
- **SC-007**: The three work streams (extraction+database, analysis, refinement+delivery) can each be tested in isolation using fixed inputs, enabling three people to develop in parallel without blocking each other.

## Assumptions

- **Output language**: Resolved (FR-019) — the summary text and audio are always produced in Traditional Chinese.
- **Movie rating source**: Resolved (FR-013) — the movie rating is the average of the stored numeric review ratings; the sentiment score is reported separately.
- **Aspect-level reporting**: Resolved (FR-014) — the response includes both an overall sentiment score and a per-aspect sentiment breakdown.
- **Audio delivery**: The audio is returned in a common playable format embedded in or referenced by the single response bundle; exact transport (inline vs. retrievable reference) is an implementation detail for planning.
- **Single user interaction**: One request yields one result bundle; no multi-turn conversation state is required for the first version.
- **Authentication**: Not in scope for the first version; the service is assumed to sit behind the team's existing/staging access controls.
- **Data scale**: The initial dataset is a small seeded/mock set sufficient to demonstrate the pipeline; large-scale catalog ingestion is out of scope for the first version.
- **External capabilities**: Sentiment analysis is provided by an external cloud service; summary refinement is provided by a language model; speech is provided by a text-to-speech capability. Specific vendor/runtime choices (e.g., the requested cloud sentiment service, web framework) are deferred to the planning phase.
- **Team division**: The feature is intentionally structured into three independently testable user stories so three contributors can own one stream each.
