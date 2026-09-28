from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class Lifecycle(StrEnum):
    experimental = "experimental"
    active = "active"
    deprecated = "deprecated"
    retired = "retired"


class ApplicationCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
        description="Unique slug, lowercase letters, digits and dashes.",
    )
    description: str = Field(default="", max_length=2000)
    owner_team: str = Field(min_length=1, max_length=100)
    owner_email: EmailStr
    repo_url: HttpUrl | None = None
    lifecycle: Lifecycle = Lifecycle.active


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    owner_team: str
    owner_email: str
    repo_url: str
    lifecycle: Lifecycle
    created_by: str
    created_at: datetime
