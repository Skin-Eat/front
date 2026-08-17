import uuid

from pydantic import BaseModel, ConfigDict

from app.models.profile import ConstraintType, SkinType


class ConstraintIn(BaseModel):
    type: ConstraintType
    ingredient_name: str


class ProfileCreate(BaseModel):
    nickname: str
    skin_type: SkinType
    concerns: list[str] = []
    constraints: list[ConstraintIn] = []


class ConstraintOut(ConstraintIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nickname: str
    skin_type: SkinType | None
    concerns: list[str]
    constraints: list[ConstraintOut] = []
