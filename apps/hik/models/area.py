from pydantic import Field

from .common import BaseModel


class AreaFilter(BaseModel):
    """Area filter model"""

    parentAreaID: str | None = Field(
        None,
        description="Parent area ID to get corresponding child area list. Empty or '-1' includes all areas",
        max_length=32,
    )
    includeSubArea: str | None = Field(
        None,
        description="Whether to get child areas: 0 (only parent area), -1 (all child areas under parent), 1 (only direct child areas under parent)",
        max_length=2,
    )


class BriefArea(BaseModel):
    """Brief area model"""

    id: str = Field(..., description="Area ID")
    name: str = Field(..., description="Area name")
    parentAreaID: str | None = Field(None, description="Parent area ID")
    existSubArea: int = Field(
        ..., description="Whether there are sub areas: 0 (no), 1 (yes)"
    )
