"""
Háztartási felhasználó-adminisztráció Pydantic-sémái.
"""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


AssignableHouseholdRole = Literal[
    "viewer",
    "editor",
    "admin",
]


class HouseholdUserCreateRequest(BaseModel):
    email: EmailStr

    display_name: str = Field(
        min_length=1,
        max_length=150,
    )

    password: str = Field(
        min_length=12,
        max_length=256,
    )

    role: AssignableHouseholdRole = "viewer"


class HouseholdUserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    user_id: int
    email: EmailStr
    display_name: str
    user_is_active: bool

    membership_id: int
    role: str
    membership_is_active: bool

    joined_at: datetime


class HouseholdUserUpdateRequest(BaseModel):
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    role: AssignableHouseholdRole | None = None

    membership_is_active: bool | None = None
