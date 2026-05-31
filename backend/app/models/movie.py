from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.lib.aspects import ASPECT_MAP

VALID_ASPECTS = list(ASPECT_MAP.keys())


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_title = Column(String, nullable=False, index=True)
    normalized_title = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    aliases = relationship("MovieAlias", back_populates="movie", cascade="all, delete-orphan")


class MovieAlias(Base):
    __tablename__ = "movie_aliases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    alias_title = Column(String, nullable=False)
    normalized_alias = Column(String, nullable=False, index=True)

    movie = relationship("Movie", back_populates="aliases")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    aspect = Column(String, nullable=False)
    rating = Column(Float, nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("rating >= 1.0 AND rating <= 5.0", name="ck_review_rating_range"),
        CheckConstraint(
            "aspect IN ('plot', 'acting', 'visuals', 'sound', 'pacing')",
            name="ck_review_aspect_valid",
        ),
    )

    movie = relationship("Movie", back_populates="reviews")
