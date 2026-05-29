from fastapi import FastAPI

app = FastAPI(
    title="電影評論情緒分析與語音敘述後端服務",
    description="NLP Final Project Backend Service",
    version="1.0.0"
)

@app.get("/health", tags=["Health"])
def health_check():
    """健全狀態檢查，確認後端伺服器正常運作"""
    return {"status": "healthy"}