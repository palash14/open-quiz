# src/app/routes/auth.py
from fastapi import APIRouter
# from src.app.schemas.quiz import QuizCreate, QuizOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login():
    """
    Do login.
    """
    pass

