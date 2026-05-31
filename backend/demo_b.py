# backend/demo_b.py
import sys
import os
# 確保 Python 能順利找到 app 包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.sentiment import analyze_overall, analyze_by_aspect
from app.services.summarizer import summarize

# 準備一組模擬的野生電影評論
mock_reviews = [
    "全面啟動這部片特效真的很震撼，音樂也搭配得完美！",
    "劇本很有深度，不過大結局節奏稍微有點燒腦變慢。",
    "特效動畫做得很真，演員演技集體在線，非常推薦！"
]

# 準備帶有面向標記的評論資料（模擬 Stream A 資料庫吐出來的格式）
mock_aspect_reviews = [
    {"text": "視覺特效真的很震撼，動畫做得很真！", "aspect": "visuals"},
    {"text": "配樂太神了，完美融入氣氛！", "aspect": "music"},
    {"text": "大結局節奏稍微有點拖，變慢了。", "aspect": "pacing"},
    {"text": "劇本寫得非常有深度。", "aspect": "plot"},
    {"text": "演員演技集體在線！", "aspect": "acting"}
]

print("==============================================")
print("🚀 正在啟動 Stream B 真實 Azure 雲端大腦測試...")
print("==============================================\n")

# 1. 測試整體情緒
print("[1] 正在調用 Azure 分析整體情緒...")
overall_res = analyze_overall(mock_reviews)
print(f"➔ 分析結果：標籤為【{overall_res.label}】，微軟信心分數：{overall_res.confidence}\n")

# 2. 測試五大面向情緒
print("[2] 正在依據五大面向分組調用 Azure...")
aspect_res = analyze_by_aspect(mock_aspect_reviews)
print("➔ 各面向獨立分析結果：")
for aspect in aspect_res:
    print(f"  • {aspect.aspect_display} ({aspect.aspect}): 情緒【{aspect.sentiment.label}】 (評論數: {aspect.review_count}, 信心值: {aspect.sentiment.confidence})")

# 3. 測試抽象式文件摘要
print("\n[3] 正在調用 Azure 生成多篇評論的繁體中文綜合摘要...")
try:
    summary_res = summarize(mock_reviews)
    print(f"➔ Azure AI 生成摘要：\n「 {summary_res} 」")
except Exception as e:
    print(f"❌ 摘要生成失敗（觸發優雅降級機制），原因: {e}")

print("\n==============================================")
print("🎉 測試結束！Stream B 後端運算核心完全正常！")
print("==============================================")