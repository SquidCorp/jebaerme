"""Health response schema."""

from pydantic import BaseModel, Field


class Health(BaseModel):
    status: str = Field(description="Service health status.")
    env: str = Field(description="Active application environment.")
