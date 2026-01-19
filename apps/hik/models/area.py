from pydantic import Field

from .common import BaseModel


class AreaFilter(BaseModel):
    """Area filter model"""

    includeSubArea: str | None = Field(None, max_length=64)
    parent_id: str | None = Field(None, alias="parentAreaID", max_length=32)


class BriefArea(BaseModel):
    """Brief area model"""

    id: str = Field(..., description="Area ID")
    name: str = Field(..., description="Area name")
    parentAreaID: str | None = Field(None, description="Parent area ID")
    existSubArea: int = Field(
        ..., description="Whether there are sub areas: 0 (no), 1 (yes)"
    )
