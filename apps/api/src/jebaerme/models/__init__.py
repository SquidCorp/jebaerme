"""Pydantic schemas and settings. No I/O."""

from pydantic import BaseModel, Field

from jebaerme.models.env import env


class Health(BaseModel):
    status: str = Field(description="Service health status.")
    env: str = Field(description="Active application environment.")


__all__ = ["Health", "env"]
