from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class Tags(str, Enum):
    study = "учёба"
    personal = "личное"
    plans = "планы"


class Todo(BaseModel):
    title: str = Field(min_length=3, max_length=200, default="Задача")
    details: str = Field(max_length=500, default="Описание задачи")
    completed: bool = Field(default=False)
    tag: Tags = Field(default=Tags.plans)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Задача",
                    "details": "Описание задачи",
                    "completed": False,
                    "tag": "планы"
                }
            ]
        }
    }
