# 電影評論情緒分析與語音敘述後端服務

對話式電影評論分析 API:前端傳一句話(例如「幫我查看看全面啟動」),後端提取電影名稱、
查詢資料庫中的多面向評論與評分,呼叫 Azure 進行情緒分析與摘要,計算電影評分,再請 LLM
修飾摘要,最後用文字轉語音產生音檔,把「評分 + 情緒 + 摘要文字 + 音檔」一起回傳給前端。

> 完整規格與設計文件位於 `specs/001-movie-sentiment-api/`(spec / plan / research /
> data-model / contracts / quickstart / tasks)。本 README 為 plan 與 tasks 的中文摘要。

---

## 1. 功能流程

```
使用者訊息
  → 提取電影名稱        (找不到電影名稱 → status=no_movie_in_message)
  → 資料庫正規化查詢    (查無此片     → status=movie_not_found)
  → 取得評論            (沒有評論     → status=insufficient_data)
  → Azure 情緒分析(整體 + 五大面向)
  → Azure 摘要 → 原始摘要
  → 平均評分(1–5)→ 電影評分
  → LLM 修飾 → 修飾後摘要   (失敗 → 退回原始摘要,加 warning)
  → Azure 文字轉語音 → 音檔  (失敗 → 音檔為 null,加 warning)
  → 回傳完整 ResultBundle(status=ok)
```

## 2. 技術選型(來自 plan.md / research.md)

| 項目 | 選擇 |
|------|------|
| 語言 | Python 3.11+ |
| Web 框架 | FastAPI + Uvicorn + Pydantic |
| 資料庫 | SQLite(透過 SQLAlchemy;之後可換 PostgreSQL,只改連線字串) |
| 情緒分析 | Azure AI Language — Sentiment Analysis |
| 摘要 | Azure AI Language — Document Summarization(abstractive) |
| 電影名稱提取 / LLM 修飾 | Azure OpenAI |
| 文字轉語音 | Azure AI Speech(zh-TW 神經語音,輸出 MP3) |
| 測試 | pytest + FastAPI TestClient;Azure 實連測試用 `RUN_AZURE=1` 隔離 |
| 輸出語言 | 一律繁體中文 |

**重要設計決策:**
- **電影名稱提取**:先用括號/引號(《》「」"")的啟發式規則,抓不到再交給 Azure OpenAI。
- **面向情緒**:固定五大面向(劇情 / 演技 / 視覺·特效 / 音效·配樂 / 節奏)。評論本身已標記
  面向,**依面向分組後各跑一次 Azure 情緒分析**(不使用 Azure 自動抽取面向的 Opinion Mining,
  以確保剛好對應這五個面向)。
- **情緒表示**:標籤(positive / neutral / negative)+ 0–1 信心值,整體與各面向皆有。
- **電影評分**:資料庫中 1–5 評分的平均,四捨五入到小數一位(如 4.3),與情緒分數分開。
- **音檔交付**:base64 內嵌在單一 JSON 回應中(一次請求拿到全部)。
- **優雅降級**:LLM 修飾或 TTS 失敗時,不讓整個請求失敗;回傳已有結果,缺的欄位設 null,
  並在 `warnings[]` 標示。

## 3. 專案結構

```text
backend/
├── app/
│   ├── main.py                 # FastAPI 入口、掛載路由、GET /health
│   ├── config.py               # 環境設定(Azure 金鑰、DB URL、TTS 語音)
│   ├── api/routes.py           # POST /api/v1/movie-insight        [Stream C]
│   ├── schemas/                # Pydantic:ConversationRequest、ResultBundle 等
│   ├── models/movie.py         # SQLAlchemy:Movie / MovieAlias / Review [Stream A]
│   ├── db/
│   │   ├── database.py         # engine / session / Base            [Stream A]
│   │   └── seed.py             # 範例電影與評論                      [Stream A]
│   ├── services/
│   │   ├── extraction.py       # 電影名稱提取(啟發式 + LLM)        [Stream A]
│   │   ├── repository.py       # 正規化查詢、取得評論                [Stream A]
│   │   ├── sentiment.py        # Azure 情緒:整體 + 各面向           [Stream B]
│   │   ├── summarizer.py       # Azure 摘要                          [Stream B]
│   │   ├── scoring.py          # 1–5 平均評分                        [Stream B]
│   │   ├── refiner.py          # LLM 修飾                            [Stream C]
│   │   ├── tts.py              # Azure 文字轉語音 → mp3              [Stream C]
│   │   └── pipeline.py         # 串接流程 + 狀態分支 + 降級          [Stream C]
│   └── lib/                    # normalize() 等共用工具
└── tests/
    ├── unit/                   # 各 Stream 單元測試(mock 外部服務)
    ├── contract/              # 請求/回應 schema 一致性測試
    └── integration/           # 實連 Azure(RUN_AZURE=1)
```

## 4. API 介面(來自 contracts/http-api.md)

### `POST /api/v1/movie-insight`

請求:

```json
{ "message": "幫我查看看全面啟動這部電影" }
```

成功回應(`status: "ok"`):

```json
{
  "status": "ok",
  "matched_movie": { "id": 1, "canonical_title": "全面啟動" },
  "movie_rating": 4.3,
  "overall_sentiment": { "label": "positive", "confidence": 0.87 },
  "aspect_sentiments": [
    { "aspect": "plot", "aspect_display": "劇情", "sentiment": { "label": "positive", "confidence": 0.91 }, "review_count": 4 }
    /* 其餘四個面向:演技、視覺/特效、音效/配樂、節奏 */
  ],
  "summary_text": "這部電影在視覺與劇情上表現突出……",
  "audio_base64": "<base64 mp3>",
  "audio_format": "mp3",
  "warnings": []
}
```

其他 `status`(皆回 HTTP 200):

| status | 意義 |
|--------|------|
| `no_movie_in_message` | 訊息中找不到電影名稱 |
| `movie_not_found` | 有提取到名稱但資料庫查無此片 |
| `insufficient_data` | 找到電影但沒有任何評論 |

`message` 為空字串 → HTTP 400;核心階段(DB / 情緒 / 摘要)不可用且無法產生部分結果 → 502/503。

## 5. 三人分工(來自 contracts/internal-services.md)

三條 user story 互相獨立、可各自用 mock 測試,對應三位開發者:

| 負責人 | Stream / Story | 範圍 | 對外函式 |
|--------|----------------|------|----------|
| **A** | US1(P1) | 對話解析 + 名稱提取 + 資料庫 | `extract_movie_title()`、`find_movie()`、`get_reviews()`、`seed()` |
| **B** | US2(P2) | 情緒分析 + 摘要 + 評分 | `analyze_overall()`、`analyze_by_aspect()`、`summarize()`、`average_rating()` |
| **C** | US3(P3) | LLM 修飾 + 語音 + 組裝回應 | `refine_summary()`、`synthesize()`、`run_pipeline()`、API 路由 |

> **關鍵**:動工前三人先一起把 `contracts/internal-services.md` 的函式簽名敲定,各自用
> mock 模擬別人的輸出,就能平行開發、最後由 C 整合。

## 6. 任務清單(來自 tasks.md,共 35 項 T001–T035)

### Phase 1:Setup(共用基礎)
- **T001** 建立 `backend/` 目錄結構
- **T002** 建立 `requirements.txt`
- **T003** [P] 建立 `.env.example`(Azure 金鑰、DB URL、TTS 語音)
- **T004** [P] 設定 ruff/black 與 pytest(`RUN_AZURE` marker)

### Phase 2:Foundational(阻塞前置,所有 story 都依賴)
- **T005** `config.py` 環境設定載入
- **T006** `db/database.py` engine / session / Base
- **T007** [P] `lib/aspects.py` 五大面向代碼 + 中文顯示對照
- **T008** [P] `schemas/common.py` 情緒標籤列舉 + `SentimentResult`
- **T009** `main.py` FastAPI 骨架 + `GET /health`

> ✅ 檢查點:基礎完成後,A/B/C 三條 story 可開始平行開發。

### Phase 3:US1 / Stream A — 對話解析 + 資料庫(P1 🎯 MVP)
- **T010** [P] [US1] `test_repository.py` 正規化查詢單元測試
- **T011** [P] [US1] `test_extraction.py` 名稱提取單元測試(mock LLM)
- **T012** [P] [US1] `models/movie.py` Movie / MovieAlias / Review 模型
- **T013** [P] [US1] `lib/normalize.py` `normalize()` 工具
- **T014** [US1] `services/repository.py` `find_movie()` + `get_reviews()`(依賴 T012、T013)
- **T015** [US1] `services/extraction.py` `extract_movie_title()`(依賴 T005)
- **T016** [US1] `db/seed.py` 載入 ≥3 部範例電影與面向評論(依賴 T012)

### Phase 4:US2 / Stream B — 情緒 + 摘要 + 評分(P2)
- **T017** [P] [US2] `test_scoring.py` 平均評分單元測試
- **T018** [P] [US2] `test_sentiment.py` 情緒彙整單元測試(mock Azure)
- **T019** [P] [US2] `test_summarizer.py` 摘要單元測試(mock Azure)
- **T020** [P] [US2] `schemas/analysis.py` `AspectSentiment` / `AnalysisResult`(依賴 T008)
- **T021** [P] [US2] `services/scoring.py` `average_rating()`
- **T022** [US2] `services/sentiment.py` `analyze_overall()` + `analyze_by_aspect()`(依賴 T005、T007、T008)
- **T023** [US2] `services/summarizer.py` `summarize()`(依賴 T005)

### Phase 5:US3 / Stream C — 修飾 + 語音 + 組裝(P3)
- **T024** [P] [US3] `test_movie_insight_contract.py` API 合約測試
- **T025** [P] [US3] `test_pipeline.py` 流程狀態分支測試(全 mock)
- **T026** [P] [US3] `test_refiner_tts.py` 修飾退回 + TTS 失敗降級測試
- **T027** [P] [US3] `schemas/bundle.py` `ConversationRequest` + `ResultBundle`(依賴 T008、T020)
- **T028** [P] [US3] `services/refiner.py` `refine_summary()`(依賴 T005)
- **T029** [P] [US3] `services/tts.py` `synthesize()`(依賴 T005)
- **T030** [US3] `services/pipeline.py` `run_pipeline()` 串接 + 狀態分支 + 降級(依賴 T014、T015、T021、T022、T023、T027、T028、T029)
- **T031** [US3] `api/routes.py` `POST /api/v1/movie-insight` + 掛載到 `main.py`(依賴 T030)

### Phase 6:Polish(跨領域收尾)
- **T032** [P] `test_pipeline_live.py` 實連 Azure 整合測試(`RUN_AZURE=1`)
- **T033** [P] `main.py` 加上請求/錯誤日誌與例外處理
- **T034** 執行 `quickstart.md` 冒煙測試 + 四個邊界案例
- **T035** 對照 SC-001 做效能檢查(完整回應 < 10 秒,95% 請求達標)

## 7. 依賴與平行開發

- **Setup → Foundational** 必須先完成,且 Foundational 阻塞所有 story。
- Foundational 完成後:
  - Stream A:T010–T016
  - Stream B:T017–T023
  - Stream C:T024–T029(其中 T030–T031 需等 A、B 的 service 完成)
- US1、US2 完全獨立;US3 僅 `run_pipeline`(T030)需整合 A+B,其餘 US3 任務(schema、
  refiner、TTS、合約/單元測試)可立即開工。

### 建議實作順序
1. **MVP**:Setup → Foundational → US1(對話查電影即可 demo)。
2. 加 US2(評分 + 情緒 + 摘要)。
3. 加 US3(LLM 修飾 + 語音 + 完整 bundle)。

## 8. 快速開始(詳見 quickstart.md)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 填入 Azure 金鑰與端點

python -m app.db.seed         # 建表並載入範例資料
uvicorn app.main:app --reload # 啟動服務
```

冒煙測試:

```bash
curl -s -X POST http://localhost:8000/api/v1/movie-insight \
  -H 'Content-Type: application/json' \
  -d '{"message":"幫我查看看全面啟動這部電影"}' | jq
```

測試:

```bash
pytest tests/unit                    # 各 Stream 單元測試(全 mock,不需 Azure)
pytest tests/contract                # 合約測試
RUN_AZURE=1 pytest tests/integration # 實連 Azure(需金鑰)
```
