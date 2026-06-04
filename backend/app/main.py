from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 👈 匯入跨域安全中間件
from dotenv import load_dotenv                      # 👈 匯入環境變數載入器

# 🔥 【關鍵修復】在伺服器開機第一秒強迫吞下 .env 的 Azure 真實金鑰！
# 徹底解決每次換電影都噴 "目前摘要服務暫時無法提供" 以及情緒分析集體中立的暗礁
load_dotenv()

from app.api.route import router

app = FastAPI(
    title="電影評論情緒分析與語音敘述後端服務",
    description="NLP Final Project Backend Service",
    version="1.0.0"
)

# 🌐 【跨域解鎖】大開本機連線門戶，允許前端 Port 5500 的 fetch 請求無阻礙進場
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 允許任何本地端來源進行網頁連線
    allow_credentials=True,
    allow_methods=["*"],            # 允許所有 HTTP 方法 (GET, POST 等)
    allow_headers=["*"],            # 允許所有封包標頭欄位
)

# 掛載路由群組
app.include_router(
    router,
    prefix="/api/v1"
)

@app.get("/health", tags=["Health"])
def health_check():
    """健全狀態檢查，確認後端伺服器正常運作"""
    return {"status": "healthy"}