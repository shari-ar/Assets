from __future__ import annotations

from datetime import datetime

from ninja import Field, Schema
from pydantic import ConfigDict


class LoginRequest(Schema):
    email: str
    password: str


class RegisterRequest(Schema):
    full_name: str = Field(alias="fullName")
    email: str
    password: str


class TokenResponse(Schema):
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime


class LoginResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    role: str


class RefreshResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    role: str


class UserResponse(Schema):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    email: str
    full_name: str = Field(alias="fullName")
    role: str
