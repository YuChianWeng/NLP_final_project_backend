<!-- SPECKIT START -->
Active feature: 001-movie-sentiment-api (Conversational Movie Review Sentiment & Narration Service).
For technologies, project structure, contracts, and shell commands, read the current plan:
`specs/001-movie-sentiment-api/plan.md` (plus research.md, data-model.md, contracts/, quickstart.md).

Stack: Python 3.11+ / FastAPI / SQLAlchemy + SQLite / Azure AI Language (sentiment + summarization),
Azure OpenAI (title extraction + LLM refinement), Azure Speech (TTS). Output is Traditional Chinese.
Work is split into three parallel streams: A (extraction + database), B (analysis: sentiment/summary/rating),
C (LLM refinement + TTS + response assembly).
<!-- SPECKIT END -->
