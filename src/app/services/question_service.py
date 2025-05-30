from typing import List, Optional
from slugify import slugify
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.app.models.question import Question
from src.app.models.choice import Choice
from src.app.schemas.question import QuestionCreate, QuestionUpdate
from src.app.schemas.choice import ChoiceSync
from src.app.services.base_service import BaseService
from src.app.models.user import User
from src.app.models.category import Category
from src.app.utils.exceptions import ValidationException, RecordNotFoundException


class QuestionService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db, Question)

    def generate_slug(self, title: str) -> str:
        """Generate a slug based on the question title and category_id."""
        return slugify(title)

    def create(self, payload: QuestionCreate) -> Question:
        """Create a new question with associated choices."""
        slug = self.generate_slug(f"{payload.question}-{payload.category_id}")

        # Check if question with same slug exists
        existing = self.find_one(slug=slug)
        if existing:
            raise ValidationException(f"Question already exists `{payload.question}` in this category id {payload.category_id}.")

        # Create the Question instance
        question = Question(
            slug=slug,
            question=payload.question,
            category_id=payload.category_id,
            question_type=payload.question_type,
            difficulty=payload.difficulty,
            references=payload.references,
            user_id=payload.user_id,
        )
        self.db.add(question)
        self.db.flush()  # Get question.id without committing

        # sync the choices
        self.sync_choices(question_id=question.id, choices_data=payload.choices)

        return question

    def update(self, question_id: int, payload: QuestionUpdate) -> Question:
        """Update an existing question."""
        # Find the question by ID
        question = self.find_by_id(record_id=question_id)
        if not question:
            raise RecordNotFoundException("Question not found.")

        # Check if question with same slug exists
        slug = self.generate_slug(f"{payload.question}-{payload.category_id}")
        existing = self.find_one(Question.id != question_id, slug=slug)
        if existing:
            raise ValidationException("Question already exists.")

        # Update the fields of the question
        for key, value in payload.dict(exclude_unset=True).items():
            if hasattr(question, key):
                setattr(question, key, value)

        # If choices are provided, sync them
        if payload.choices is not None:
            self.sync_choices(question_id=question.id, choices_data=payload.choices)

        self.db.flush()  # Flush to get changes reflected
        return question

    def delete(self, question_id: int) -> None:
        """Soft delete a question by setting deleted_at timestamp."""
        # Find the question by ID
        question = self.find_by_id(question_id)
        if not question:
            raise RecordNotFoundException("Question not found.")

        # Soft delete the question by setting the deleted_at timestamp
        question.deleted_at = datetime.now(timezone.utc)
        self.db.flush()  # Flush to commit the change

    def sync_choices(self, question_id: int, choices_data: List[ChoiceSync]) -> None:
        """
        Sync choices for a given question:
        - Update existing choices based on the provided 'id' or 'option_text'.
        - Create new choices if they don't exist.
        - Delete choices that are not provided in the new data.

        :param question_id: The ID of the question whose choices need to be updated.
        :param choices_data: A list of choice data to be inserted or updated for the question.
        """
        # Fetch the current choices for the question from the database
        current_choices = (
            self.db.query(Choice).filter(Choice.question_id == question_id).all()
        )

        # Convert the current choices into a dictionary with 'id' as the key
        current_choices_dict = {choice.id: choice for choice in current_choices}

        # A list to store new or updated choices
        new_choices = []
        # A set of choice ids to track which ones were handled
        existing_choice_ids = set()

        # Iterate through the provided choices data (choices_data) and decide whether to update or create new choices
        for choice_data in choices_data:
            # If choice_data contains 'id', we will attempt to find and update the choice
            if "id" in choice_data:
                existing_choice = current_choices_dict.get(choice_data.id)

                if existing_choice:
                    # Update the existing choice
                    existing_choice.option_text = choice_data.option_text
                    existing_choice.is_correct = choice_data.is_correct
                    existing_choice_ids.add(choice_data.id)
                else:
                    # If we can't find the choice by 'id', we create a new choice
                    new_choices.append(
                        Choice(
                            question_id=question_id,
                            option_text=choice_data.option_text,
                            is_correct=choice_data.is_correct,
                        )
                    )
                    existing_choice_ids.add(choice_data.id)
            else:
                # Create a new choice if no 'id' is provided (i.e., this is a new choice)
                new_choices.append(
                    Choice(
                        question_id=question_id,
                        option_text=choice_data.option_text,
                        is_correct=choice_data.is_correct,
                    )
                )
                existing_choice_ids.add(None)  # No id, mark as new choice

        # Bulk save new choices to the database
        self.db.bulk_save_objects(new_choices)

        # Delete the old choices that are no longer part of the new data
        choices_to_delete = [
            choice for choice in current_choices if choice.id not in existing_choice_ids
        ]
        if choices_to_delete:
            self.db.delete(choices_to_delete)

        # Commit changes to the database
        self.db.flush()

    def paginate_questions(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
        user_name: Optional[str] = None,
        category: Optional[str] = None,
        question: Optional[str] = None,
        response_model=None,
    ):
        builder = self.builder()

        if user_name:
            builder = builder.where_relation(User, "name", user_name)

        if category:
            builder = builder.where_relation_like(Category, "name", category)

        if question:
            builder = builder.where(Question.question.ilike(f"%{question}%"))

        return builder.order_by(sort_by, sort_order).paginate(
            page=page,
            page_size=page_size,
            response_model=response_model,
        )
