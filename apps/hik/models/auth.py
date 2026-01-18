from pydantic import Field

from .common import BaseModel


class TokenRequest(BaseModel):
    """Token request model"""

    app_key: str = Field(..., alias="appKey", min_length=1, max_length=64)
    secret_key: str = Field(..., alias="secretKey", min_length=1, max_length=64)


class TokenResponse(BaseModel):
    """Token response model"""

    access_token: str = Field(..., alias="accessToken")
    expire_time: int = Field(..., alias="expireTime")
    user_id: str = Field(..., alias="userId")
    area_domain: str | None = Field(None, alias="areaDomain")
