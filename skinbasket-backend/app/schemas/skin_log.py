from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkinLogCreate(BaseModel):
    logged_at: datetime | None = None
    trouble_level: int
    oil_level: int
    dryness_level: int
    photo_url: str | None = None
    memo: str | None = None


class SkinLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    logged_at: datetime
    trouble_level: int
    oil_level: int
    dryness_level: int
    photo_url: str | None
    memo: str | None
