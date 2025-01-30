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


# class OkAnswerSchema(Schema):
#     success = fields.Bool(required=True)


class QuizSchema(BaseModel):
    id: int = Field(...)
    question: str = Field(...)
    answer: str = Field(...)
    price: int = Field(...)
    category: str = Field(...)


# class QuizSchema(Schema):
#     id = fields.Int(required=False)
#     question = fields.Str(required=True)
#     answer = fields.Str(required=True)
#     price = fields.Int(required=True)
#     category = fields.Enum(CategoryEnum, by_value=True)

#     @validates_schema
#     def validate_answers(self, data, **kwargs):
#         if data["price"] <= 0:
#             raise ValidationError("price must be greater than 0")
#         if data.get("id", None) is not None:
#             raise ValidationError("don't provide id, it will be auto generated")


# class QuizzesListSchema(Schema):
#     quizzes = fields.Nested(QuizSchema, many=True)


# class StatusCountSchema(Schema):
#     status = fields.Str(allow_none=True)
#     count = fields.Int()


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
                    "category": "category",
                }
            ],
        }


class StatusCountSchema(BaseModel):
    status: str | None = Field(default=None)
    count: int = Field(...)


class UserSearchSchema(BaseModel):
    id: int | None = Field(...)
    vk_id: int = Field(...)


# class UserSearchSchema(Schema):
#     id = fields.Int(required=False)
#     vk_id = fields.Int(required=False)

#     @validates_schema
#     def validate_answers(self, data, **kwargs):
#         if data and data.get("id") and data.get("id") <= 0:
#             raise ValidationError("id must be greater than 0")


class UserFoundSchema(BaseModel):
    first_name: str = Field(default=None)
    second_name: str = Field(default=None)
    vk_id: int = Field(...)
