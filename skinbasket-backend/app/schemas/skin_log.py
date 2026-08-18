from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class SkinLogCreate(CamelModel):
    logged_at: datetime | None = None
    trouble_level: int = Field(ge=1, le=5)
    oil_level: int = Field(ge=1, le=5)
    dryness_level: int = Field(ge=1, le=5)
    photo_url: str | None = None
    memo: str | None = None


class SkinLogOut(CamelModel):
    id: int
    logged_at: datetime
    trouble_level: int
    oil_level: int
    dryness_level: int
    photo_url: str | None
    memo: str | None
