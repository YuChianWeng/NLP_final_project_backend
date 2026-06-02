# backend/test_pipeline_live.py
from dotenv import load_dotenv  
load_dotenv()                   

import json
import traceback
from app.db.database import SessionLocal, engine, Base  # 👈 1. 這裡同步引入 engine 與 Base
from app.services.pipeline import build_movie_insight

def test_run():
    print("==================================================")
    print("🚀 正在發動全管線總串接動態測試 (包含即時爬蟲)...")
    print("==================================================")
    
    # 🔥 2. 【核心修復大絕】在開機第一秒，強迫 SQLite 自動建好所有缺少的資料表！
    print("📦 正在檢查並初始化本地 SQLite 資料表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 資料庫結構初始化完畢！")
    print("--------------------------------------------------")
    
    # 3. 初始化本地資料庫連線 Session
    db = SessionLocal()
    
    try:
        # 4. 故意輸入一部本地資料庫絕對沒有的電影，迫使系統啟動爬蟲救援
        test_message = "我想看 Fast Furious 的評論分析"
        print(f"▼ 使用者輸入訊息：'{test_message}'")
        
        # 5. 丟進總管線
        bundle = build_movie_insight(message=test_message, db=db)
        
        print("\n==================================================")
        print("🎉 總管線執行完畢！執行結果封裝大禮包如下：")
        print("==================================================")
        print(f"➔ 回傳狀態 (status): {bundle.status}")
        print(f"➔ 識別片名 (matched_movie): {bundle.matched_movie}")
        print(f"➔ 系統警告 (warnings): {bundle.warnings}")
        print(f"➔ 語音格式 (audio_format): {bundle.audio_format}")
        
        if bundle.audio_base64:
            print(f"➔ 語音長度 (audio_base64): 已成功生成 (前50字: {bundle.audio_base64[:50]}...)")
        else:
            print("➔ 語音長度 (audio_base64): 無語音數據")
            
        print("\n▼ AI 綜合摘要文字 (summary_text)：")
        print(f"「 {bundle.summary_text} 」")
        
        if bundle.analysis:
            print("\n▼ Stream B 面向情緒分析結構 (AnalysisResult JSON)：")
            analysis_json = json.loads(bundle.analysis.model_dump_json())
            print(json.dumps(analysis_json, ensure_ascii=False, indent=2))

    except Exception as e:
        print("\n❌ 測試過程發生崩潰錯誤！詳細追蹤地圖如下：")
        print("--------------------------------------------------")
        traceback.print_exc()
        print("--------------------------------------------------")
    finally:
        # 6. 關閉資料庫連線
        db.close()
        print("\n==================================================\n")

if __name__ == "__main__":
    test_run()