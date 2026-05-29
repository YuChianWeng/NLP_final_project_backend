from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 建立資料庫引擎 (如果是 SQLite，需要額外允許多執行緒檢查)
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 建立 Session 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 ORM 模型基底類別
Base = declarative_base()

# 提供給 FastAPI 路由使用的資料庫連線生命週期管理器
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()