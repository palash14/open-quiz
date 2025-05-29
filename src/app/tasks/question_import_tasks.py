# File: src/app/tasks/question_import_tasks.py
import requests
import random
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.app.core.database import get_db
from src.app.schemas.question import QuestionCreate
from src.app.services.question_service import QuestionService
from src.app.services.category_service import CategoryService
from src.app.schemas.category import CategoryCreate
import json
from src.app.core.logger import create_logger


def fetch_and_store_questions():
    logger = create_logger("question_tasks", "question_import_tasks.log")
    print("Fetching questions...")
    category_id = random.randint(9, 32)
    response = requests.get(
        f"https://opentdb.com/api.php?amount=50&category={category_id}"
    )
    if response.status_code != 200:
        print("Failed to fetch questions")
        return

    data = response.json().get("results", [])
    db_gen = get_db()
    db: Session = next(db_gen)
    inserted_count = 0
    question_service = QuestionService(db)
    category_service = CategoryService(db)
    if not data:
        print("No questions returned from API")
        return

    category_name = data[0]["category"]
    category_data = category_service.find_one(name=category_name)
    if not category_data:
        payload = CategoryCreate(name=category_name)
        category_data = category_service.create(payload)

    for q in data:
        question_text = q["question"]
        # Check if the question already exists
        exists = question_service.find_one(
            question=question_text, category_id=category_data.id
        )
        if exists:
            continue

        try:
            correct_answer = q["correct_answer"]
            incorrect_answers = q["incorrect_answers"]

            # Build choices
            choices = [{"option_text": correct_answer, "is_correct": True, "id": None}]
            choices += [
                {"option_text": ans, "is_correct": False, "id": None} for ans in incorrect_answers
            ]

            question_type = "boolean"
            if q["type"] == "multiple":
                question_type = "multiple_choice"

            payload = QuestionCreate(
                question=question_text,
                category_id=category_data.id,
                question_type=question_type,
                difficulty=q["difficulty"],
                references="opentdb.com",
                choices=choices,
                user_id=1
            ) 
            question_obj = question_service.create(payload.model_copy(update={"user_id": 1}))
            db.add(question_obj)
            inserted_count += 1
        except IntegrityError as e:
            logger.error(e)
            db.rollback()
            continue

    db.commit()
    db.close()
    print(f"Inserted {inserted_count} new questions.")
