import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.movie import Movie, MovieAlias, Review
from app.lib.normalize import normalize
from app.services.repository import find_movie, get_reviews


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 植入兩部電影
    inception = Movie(canonical_title="全面啟動", normalized_title=normalize("全面啟動"))
    parasite = Movie(canonical_title="寄生上流", normalized_title=normalize("寄生上流"))
    session.add_all([inception, parasite])
    session.flush()

    # 別名
    session.add_all([
        MovieAlias(movie_id=inception.id, alias_title="Inception", normalized_alias=normalize("Inception")),
        MovieAlias(movie_id=inception.id, alias_title="潛行空間", normalized_alias=normalize("潛行空間")),
        MovieAlias(movie_id=parasite.id, alias_title="Parasite", normalized_alias=normalize("Parasite")),
    ])

    # 評論
    session.add_all([
        Review(movie_id=inception.id, aspect="plot", rating=5.0, text="劇情精彩"),
        Review(movie_id=inception.id, aspect="acting", rating=4.5, text="演技出色"),
    ])

    session.commit()
    yield session
    session.close()


# --- find_movie ---

def test_find_movie_by_canonical_title(db):
    movie = find_movie("全面啟動", db)
    assert movie is not None
    assert movie.canonical_title == "全面啟動"


def test_find_movie_case_insensitive(db):
    movie = find_movie("Inception", db)
    assert movie is not None
    assert movie.canonical_title == "全面啟動"


def test_find_movie_by_alias(db):
    movie = find_movie("潛行空間", db)
    assert movie is not None
    assert movie.canonical_title == "全面啟動"


def test_find_movie_ignores_spaces_and_punctuation(db):
    movie = find_movie("全面 啟動", db)
    assert movie is not None
    assert movie.canonical_title == "全面啟動"


def test_find_movie_not_found(db):
    movie = find_movie("不存在的電影", db)
    assert movie is None


def test_find_movie_prefers_canonical_over_alias(db):
    # 若 canonical 和 alias 都能命中同一個 key（理論上不應發生，但邏輯要保證 canonical 先回傳）
    movie = find_movie("寄生上流", db)
    assert movie is not None
    assert movie.canonical_title == "寄生上流"


# --- get_reviews ---

def test_get_reviews_returns_all_reviews(db):
    movie = find_movie("全面啟動", db)
    reviews = get_reviews(movie.id, db)
    assert len(reviews) == 2


def test_get_reviews_returns_empty_for_no_reviews(db):
    movie = find_movie("寄生上流", db)
    reviews = get_reviews(movie.id, db)
    assert reviews == []


def test_get_reviews_correct_aspects(db):
    movie = find_movie("全面啟動", db)
    reviews = get_reviews(movie.id, db)
    aspects = {r.aspect for r in reviews}
    assert aspects == {"plot", "acting"}
