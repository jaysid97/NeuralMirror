from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentIn(BaseModel):
    content: str = Field(min_length=1)
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("Embedding vector must not be empty")
        return v


class SearchRequest(BaseModel):
    query_embedding: list[float]
    k: int = Field(default=5, ge=1, le=100)

    @field_validator("query_embedding")
    @classmethod
    def validate_query_embedding(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("Embedding vector must not be empty")
        return v


class SearchResult(BaseModel):
    id: int
    content: str
    metadata: dict[str, Any]
    score: float


class HealthResponse(BaseModel):
    status: str


class DocumentCreated(BaseModel):
    id: int


class IngestRequest(BaseModel):
    text: str = Field(min_length=1)


class SearchQuery(BaseModel):
    id: int
    content: str
    score: float
