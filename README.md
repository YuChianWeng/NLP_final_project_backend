# 電影評論情緒分析與語音敘述後端服務

這是一個對話式電影評論分析 API。前端送出一句自然語言，例如「幫我查看看全面啟動這部電影」，後端會抽出電影名稱、查詢評論資料、進行情緒與面向分析、產生摘要，最後把摘要轉成語音，回傳給前端顯示。

目前專案包含：

- FastAPI 後端 API
- SQLite + SQLAlchemy 資料庫
- Azure OpenAI 片名抽取與摘要潤飾
- Azure AI Language 情緒分析與摘要
- Azure Speech 文字轉語音
- Metacritic crawler fallback
- 靜態 HTML/CSS/JS 前端頁面

完整規格文件位於 `specs/001-movie-sentiment-api/`。本 README 以目前程式實作為主。

---

## 1. 後端流程

```text
使用者訊息
  -> FastAPI 接收 POST /api/v1/movie-insight
  -> extract_movie_title() 抽出電影名稱
  -> find_movie() 查詢資料庫電影正名與別名
  -> get_reviews() 取得資料庫評論
  -> 如果資料庫沒有資料，嘗試 Metacritic crawler 即時抓評論
  -> analyze_overall() 分析整體情緒
  -> analyze_by_aspect() 分析五大面向情緒
  -> average_rating() 計算 1-5 平均評分
  -> summarize() 產生原始摘要
  -> refine_summary() 用 LLM 潤飾繁體中文摘要
  -> synthesize() 產生 MP3 語音
  -> ResultBundle JSON 回傳給前端
```

特殊狀態：

| status | 意義 |
|--------|------|
| `ok` | 成功產生完整分析結果 |
| `no_movie_in_message` | 無法從使用者訊息抽出電影名稱 |
| `movie_not_found` | 資料庫與 crawler 都找不到該電影 |
| `insufficient_data` | 找到電影，但沒有可分析評論 |

LLM 潤飾、摘要或 TTS 失敗時，系統會盡量保留可用結果，並在 `warnings` 裡標示降級原因。

---

## 2. 專案結構

```text
backend/
├── app/
│   ├── main.py                 # FastAPI 入口、CORS、/health、掛載 router
│   ├── config.py               # .env 設定：DB URL、Azure key、TTS voice
│   ├── api/
│   │   └── route.py            # POST /api/v1/movie-insight
│   ├── db/
│   │   ├── database.py         # SQLAlchemy engine / SessionLocal / Base / get_db()
│   │   └── seed.py             # 建立資料表並匯入範例電影評論
│   ├── models/
│   │   └── movie.py            # Movie / MovieAlias / Review ORM model
│   ├── schemas/
│   │   ├── common.py           # SentimentLabel / SentimentResult
│   │   ├── analysis.py         # AnalysisResult / AspectSentiment
│   │   └── bundle.py           # ConversationRequest / ResultBundle
│   ├── services/
│   │   ├── extraction.py       # 電影名稱抽取
│   │   ├── repository.py       # 電影與評論查詢
│   │   ├── sentiment.py        # Azure 情緒分析
│   │   ├── summarizer.py       # Azure 摘要
│   │   ├── scoring.py          # 平均評分
│   │   ├── refiner.py          # Azure OpenAI 摘要潤飾
│   │   ├── tts.py              # Azure Speech TTS
│   │   └── pipeline.py         # 串接完整後端流程
│   └── lib/
│       ├── aspects.py          # 五大面向代碼與中文顯示
│       └── normalize.py        # 片名正規化
├── crawler/                    # Metacritic crawler 與 aspect classifier
├── tests/                      # pytest 單元測試
├── requirements.txt
└── pytest.ini

static/
├── index.html                  # 前端畫面
├── script.js                   # 呼叫後端 API、渲染結果
└── style.css
```

---

## 3. Stream A / B / C 分工

| Stream | 負責範圍 | 主要檔案 | 主要函式 |
|--------|----------|----------|----------|
| A | 使用者輸入解析、電影資料庫、評論取得 | `extraction.py`, `repository.py`, `models/movie.py`, `db/database.py`, `db/seed.py` | `extract_movie_title()`, `find_movie()`, `get_reviews()`, `seed()` |
| B | 情緒分析、面向分析、摘要、評分 | `sentiment.py`, `summarizer.py`, `scoring.py`, `schemas/analysis.py` | `analyze_overall()`, `analyze_by_aspect()`, `summarize()`, `average_rating()` |
| C | API、流程整合、LLM 潤飾、TTS、回傳格式 | `pipeline.py`, `refiner.py`, `tts.py`, `api/route.py`, `schemas/bundle.py` | `build_movie_insight()`, `refine_summary()`, `synthesize()` |

簡單來說：

```text
Stream A：找出電影和評論
Stream B：分析評論內容
Stream C：組合流程並回傳前端
```

---

## 4. 資料庫設計

本專案使用 SQLite 搭配 SQLAlchemy ORM。

| 檔案 | 角色 |
|------|------|
| `app/config.py` | 讀取 `DATABASE_URL`，預設 `sqlite:///./movie_insight.db` |
| `app/db/database.py` | 建立 `engine`、`SessionLocal`、`Base`，並提供 `get_db()` |
| `app/models/movie.py` | 定義資料表 schema |
| `app/db/seed.py` | 呼叫 `Base.metadata.create_all(bind=engine)` 建表，並匯入初始資料 |
| `app/services/repository.py` | 使用 FastAPI 傳入的 `db Session` 查詢電影與評論 |

資料表：

- `movies`：電影主表，存正式片名與正規化片名
- `movie_aliases`：電影別名，例如英文名或不同翻譯
- `reviews`：評論資料，包含面向、評分、評論文字

`database.py` 只負責連線與 Session 設定；實際建立資料表與塞入範例資料是在 `seed.py`。

---

## 5. API 介面

### `POST /api/v1/movie-insight`

請求：

```json
{
  "message": "幫我查看看全面啟動這部電影"
}
```

成功回應：

```json
{
  "status": "ok",
  "matched_movie": "全面啟動",
  "rating": 4.7,
  "analysis": {
    "overall_sentiment": {
      "label": "positive",
      "confidence": 0.91
    },
    "aspect_sentiments": [
      {
        "aspect": "plot",
        "aspect_display": "劇情",
        "sentiment": {
          "label": "positive",
          "confidence": 0.9
        },
        "review_count": 2
      }
    ]
  },
  "summary_text": "這部電影的劇情結構精密，視覺效果突出...",
  "audio_base64": "<base64 mp3>",
  "audio_format": "mp3",
  "warnings": []
}
```

目前前端讀取的欄位是：

- `data.matched_movie`
- `data.rating`
- `data.analysis.overall_sentiment`
- `data.analysis.aspect_sentiments`
- `data.summary_text`
- `data.audio_base64`

---

## 6. 環境變數

建立 `.env`：

```bash
cd backend
cp .env.example .env
```

需要填入：

```env
APP_ENV=development
DATABASE_URL=sqlite:///./movie_insight.db

AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

AZURE_LANGUAGE_API_KEY=your_azure_language_api_key
AZURE_LANGUAGE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

AZURE_SPEECH_API_KEY=your_azure_speech_api_key
AZURE_SPEECH_REGION=eastus
AZURE_SPEECH_VOICE_NAME=zh-TW-HsiaoChenNeural
```

沒有 Azure key 時，片名抽取、情緒分析、摘要潤飾與 TTS 可能無法完整運作。

---

## 7. 快速開始

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.db.seed
uvicorn app.main:app --reload
```

健康檢查：

```bash
curl http://127.0.0.1:8000/health
```

API 測試：

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/movie-insight \
  -H 'Content-Type: application/json' \
  -d '{"message":"幫我查看看全面啟動這部電影"}'
```

前端：

```text
打開 static/index.html
```

---

## 8. 測試

```bash
cd backend
pytest tests/unit
```

若要跑實際 Azure 整合測試，需要先設定 `.env`，再依測試檔需求開啟 live test。

---

## 9. 注意事項

- `seed.py` 需要手動執行，後端啟動時不會自動建表或塞資料。
- `repository.py` 不直接 import `database.py`，而是使用 route 透過 `Depends(get_db)` 傳入的 `db Session`。
- 如果只更換 SQLite / PostgreSQL 等資料庫系統，且 schema 相同，通常只需改 `DATABASE_URL`。
- 如果資料表名稱或欄位不同，必須同步修改 `models/movie.py` 與 `services/repository.py`。
- 目前程式的成功回應欄位是 `rating` 與 `analysis`，不是舊文件中的 `movie_rating`、`overall_sentiment` 頂層欄位。
