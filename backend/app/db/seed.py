from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.movie import Movie, MovieAlias, Review
from app.lib.normalize import normalize

SEED_DATA = [
    {
        "canonical_title": "全面啟動",
        "aliases": ["Inception", "潛行空間"],
        "reviews": [
            {"aspect": "plot",    "rating": 5.0, "text": "劇情層層疊套，結構極為精密，每次重看都有新發現。"},
            {"aspect": "plot",    "rating": 4.5, "text": "故事複雜但邏輯自洽，令人反覆思考夢境與現實的界線。"},
            {"aspect": "acting",  "rating": 4.5, "text": "李奧納多的表演細膩深沉，將角色的痛苦與執念詮釋得淋漓盡致。"},
            {"aspect": "visuals", "rating": 5.0, "text": "城市折疊的視覺效果震撼人心，至今仍是影史經典。"},
            {"aspect": "sound",   "rating": 5.0, "text": "Hans Zimmer 的配樂完美烘托緊張氛圍，低沉的號角聲令人難忘。"},
            {"aspect": "pacing",  "rating": 4.0, "text": "節奏張弛有度，最後一幕的平行剪輯尤其精彩。"},
        ],
    },
    {
        "canonical_title": "星際效應",
        "aliases": ["Interstellar", "星際穿越"],
        "reviews": [
            {"aspect": "plot",    "rating": 4.5, "text": "科學概念與情感敘事完美融合，父女情深催人淚下。"},
            {"aspect": "plot",    "rating": 4.0, "text": "黑洞、時間膨脹等物理概念處理得相當嚴謹，不失娛樂性。"},
            {"aspect": "acting",  "rating": 4.5, "text": "麥修·麥康納的表現真摯動人，太空艙裡看影片那幕令人心碎。"},
            {"aspect": "visuals", "rating": 5.0, "text": "黑洞視覺化參考真實物理模型，美到令人窒息。"},
            {"aspect": "sound",   "rating": 5.0, "text": "Hans Zimmer 管風琴主題曲宏偉壯闊，與宇宙的浩瀚完美契合。"},
            {"aspect": "pacing",  "rating": 3.5, "text": "第三幕稍嫌倉促，但整體仍能維持觀眾的高度專注。"},
        ],
    },
    {
        "canonical_title": "寄生上流",
        "aliases": ["Parasite", "寄生蟲", "기생충"],
        "reviews": [
            {"aspect": "plot",    "rating": 5.0, "text": "劇情轉折出乎意料，對階級差異的諷刺入木三分。"},
            {"aspect": "plot",    "rating": 5.0, "text": "每個細節都有伏筆，二刷才發現許多隱藏線索。"},
            {"aspect": "acting",  "rating": 5.0, "text": "全員演技無懈可擊，宋康昊的表演尤其層次豐富。"},
            {"aspect": "visuals", "rating": 4.5, "text": "構圖精心設計，豪宅與地下室的對比視覺化了階級鴻溝。"},
            {"aspect": "sound",   "rating": 4.0, "text": "配樂低調卻有效，刻意的靜默有時比音樂更有張力。"},
            {"aspect": "pacing",  "rating": 4.5, "text": "節奏控制精準，喜劇到驚悚的轉換毫無違和感。"},
        ],
    },
    {
        "canonical_title": "你的名字",
        "aliases": ["君の名は", "Your Name", "你的名字。"],
        "reviews": [
            {"aspect": "plot",    "rating": 4.5, "text": "靈魂互換的設定新鮮有趣，時間軸轉折令人驚艷。"},
            {"aspect": "acting",  "rating": 4.0, "text": "聲優表現自然生動，角色情感傳遞真實。"},
            {"aspect": "visuals", "rating": 5.0, "text": "新海誠的背景作畫美得像明信片，黃昏場景尤其動人。"},
            {"aspect": "sound",   "rating": 5.0, "text": "RADWIMPS 的音樂與畫面高度契合，讓情緒直接爆發。"},
            {"aspect": "pacing",  "rating": 4.0, "text": "前半輕快有趣，後半情感張力逐漸升溫，結尾令人滿足。"},
        ],
    },
]


def seed(db: Session | None = None) -> None:
    close_after = db is None
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

    try:
        if db.query(Movie).count() > 0:
            return

        for data in SEED_DATA:
            movie = Movie(
                canonical_title=data["canonical_title"],
                normalized_title=normalize(data["canonical_title"]),
            )
            db.add(movie)
            db.flush()

            for alias_title in data["aliases"]:
                db.add(MovieAlias(
                    movie_id=movie.id,
                    alias_title=alias_title,
                    normalized_alias=normalize(alias_title),
                ))

            for r in data["reviews"]:
                db.add(Review(
                    movie_id=movie.id,
                    aspect=r["aspect"],
                    rating=r["rating"],
                    text=r["text"],
                ))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    seed()
    print("Seed 完成：已植入", len(SEED_DATA), "部電影的評論資料。")
