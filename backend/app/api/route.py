from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.bundle import ConversationRequest, ResultBundle
from app.services.pipeline import build_movie_insight

router = APIRouter()

@router.post(
    "/movie-insight",
    response_model=ResultBundle
)
def movie_insight(
    request: ConversationRequest,
    db: Session = Depends(get_db)
):
    return build_movie_insight(
        request.message,
        db
    )