from typing import Generic, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field

T = TypeVar("T")


class BaseModel(PydanticBaseModel):
    """Base model with common configuration for all models"""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


class BaseResponse(BaseModel):
    """Base response model for all API responses"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        populate_by_name=True,
    )

    error_code: str = Field(..., alias="errorCode")
    message: str | None = None


class PaginatedResponse(BaseResponse, Generic[T]):
    """Generic paginated response model"""

    total_count: int = Field(..., alias="totalCount")
    page_index: int = Field(..., alias="pageIndex")
    page_size: int = Field(..., alias="pageSize")
    data: list[T] = Field(default_factory=list)
