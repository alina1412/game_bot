# from marshmallow import Schema, ValidationError, fields, validates_schema

from pydantic import BaseModel, Field

from service.dataclasses import CategoryEnum


class OkAnswerSchema(BaseModel):
    success: bool = Field()
    data: dict = Field()

    class Config:
        json_schema_extra = {
            "example": {"success": True},
            "description": "Schema for a successful operation response.",
        }


class QuizSchema(BaseModel):
    id: int | None = None
    question: str = Field(...)
    answer: str = Field(...)
    price: int = Field(gt=0)
    category: CategoryEnum = Field(...)

    class Config:
        schema_extra = [
            {
                "id": 1,
                "question": "question",
                "answer": "answer",
                "price": 100,
                "category": "common",
            }
        ]


class QuizzesListSchema(BaseModel):
    quizzes: list[QuizSchema] = Field(...)

    class Config:
        json_schema_extra = {
            "quizzes": [
                {
                    "id": 1,
                    "question": "question",
                    "answer": "answer",
                    "price": 100,
                    "category": "common",
                }
            ]
        }


class StatusCountSchema(BaseModel):
    status: str | None = Field(default=None)
    count: int = Field(...)


class UserSearchSchema(BaseModel):
    id: int | None = Field(gt=0)
    vk_id: int = Field(gt=0)


class UserFoundSchema(BaseModel):
    first_name: str = Field(default=None)
    second_name: str = Field(default=None)
    vk_id: int = Field(...)
