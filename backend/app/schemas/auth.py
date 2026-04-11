from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSummary(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    permissions: list[str] = []
    branch_ids: list[str] = []
