from sqlalchemy.orm import Session
from app.models.movie import Movie, MovieAlias, Review
from app.lib.normalize import normalize


def find_movie(extracted_title: str, db: Session) -> Movie | None:
    """正規化查表：先比對 canonical_title，再比對 alias。有衝突時優先回傳 canonical 命中。"""
    key = normalize(extracted_title)

    canonical_hit = (
        db.query(Movie)
        .filter(Movie.normalized_title == key)
        .first()
    )
    if canonical_hit:
        return canonical_hit

    alias_hit = (
        db.query(Movie)
        .join(MovieAlias, Movie.id == MovieAlias.movie_id)
        .filter(MovieAlias.normalized_alias == key)
        .first()
    )
    return alias_hit


def get_reviews(movie_id: int, db: Session) -> list[Review]:
    """回傳該電影的所有評論；空串列代表 insufficient_data。"""
    return db.query(Review).filter(Review.movie_id == movie_id).all()
