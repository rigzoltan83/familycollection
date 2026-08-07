"""
Autentikációs Pydantic-sémák.

Ezek a sémák határozzák meg a bejelentkezési kérés és
a későbbi válaszok adatformátumát.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=256,
    )


class AuthenticatedUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str
    is_platform_admin: bool


class LoginResponse(BaseModel):
    status: str
    user: AuthenticatedUserResponse


class AuthHouseholdResponse(BaseModel):
    id: int
    name: str
    slug: str
    role: str


class AuthContextResponse(BaseModel):
    user: AuthenticatedUserResponse
    households: list[AuthHouseholdResponse]
