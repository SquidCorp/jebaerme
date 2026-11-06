"""Job request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobCreate(BaseModel):
    company_name: str = Field(
        description="Name of the company that published the job ad."
    )
    ad_url: str = Field(description="Link to the job ad.")
    job_title: str = Field(description="Job title extracted by an agent.")
    full_remote: bool = Field(
        default=False,
        description="Whether the job is fully remote.",
    )
    location: str | None = Field(
        default=None,
        description="Location from the job ad.",
    )


class JobAdUrlCreate(BaseModel):
    ad_url: HttpUrl = Field(description="Link to the job ad.")


class JobUpdate(BaseModel):
    company_name: str | None = Field(
        default=None,
        description="Name of the company that published the job ad.",
    )
    ad_url: str | None = Field(default=None, description="Link to the job ad.")
    job_title: str | None = Field(
        default=None,
        description="Job title extracted by an agent.",
    )
    full_remote: bool | None = Field(
        default=None,
        description="Whether the job is fully remote.",
    )
    location: str | None = Field(
        default=None,
        description="Location from the job ad.",
    )


class JobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Job identifier.")
    company_name: str = Field(
        description="Name of the company that published the job ad."
    )
    ad_url: str = Field(description="Link to the job ad.")
    job_title: str = Field(description="Job title extracted by an agent.")
    full_remote: bool = Field(description="Whether the job is fully remote.")
    location: str | None = Field(description="Location from the job ad.")
    invitation_code: str = Field(description="Server-generated invitation code.")
    created_at: datetime = Field(description="When the job was created.")
