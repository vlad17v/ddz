from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class TodoSource(str, Enum):
    created = "Созданная"
    generated = "Сгенерированная"
    imported = "Импортированная"


class Tags(str, Enum):
    study = "Учёба"
    personal = "Личное"
    plans = "Планы"


class TodoCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    details: str = Field(default="", max_length=500)
    tag: Tags = Field(default=Tags.plans)
    source: TodoSource = Field(default=TodoSource.created)
    count_todos: int = Field(default=1, ge=1, le=100)


class TodoUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    details: str = Field(default="", max_length=500)
    completed: bool = False
    tag: Tags = Field(default=Tags.plans)
    created_at: datetime | None = None
    existing_image: str | None = None


class TodoSearchParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    skip: int = Field(default=0, ge=0)
    creation_date_start: datetime | None = None
    creation_date_end: datetime | None = None
    tag: Tags | None = None
    query: str | None = Field(default=None, max_length=200)


class TodoExportRow(BaseModel):
    id: int | None = None
    title: str
    details: str
    completed: bool = False
    tag: str = Tags.plans.value
    created_at: datetime | None = None
    completed_at: datetime | None = None
    source: str = TodoSource.imported.value
    image_path: str | None = None
    image_hash: str | None = None
    attachment_path: str | None = None


class WordFrequency(BaseModel):
    word: str
    count: int = Field(ge=1)


class UserCreate(BaseModel):
    username: str
    password: str
