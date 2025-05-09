# src/app/main.py
from fastapi import FastAPI
from src.app.routes import quiz, auth

app = FastAPI(
    title="Quiz API",
    description="An API for managing quizzes and users",
    version="1.0.0"
)



app.include_router(quiz.router)
app.include_router(auth.router)

