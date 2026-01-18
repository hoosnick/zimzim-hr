from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import BaseModel


class PersonGroup(BaseModel):
    """Person group (department) model"""

    group_id: str = Field(..., alias="groupId")
    group_name: str = Field(..., alias="groupName")
    parent_id: str | None = Field(None, alias="parentId")
    child_node_exist: bool | None = Field(None, alias="childNodeExist")
    description: str | None = None
    group_full_path: str | None = Field(None, alias="groupFullPath")


class Person(BaseModel):
    """Person model"""

    person_id: str | None = Field(None, alias="personId")
    group_id: str = Field(..., alias="groupId")
    person_code: str = Field(..., alias="personCode")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    gender: Literal[0, 1, 2] = 2  # 0=female, 1=male, 2=unknown
    phone: str | None = Field(None)
    email: str | None = None
    description: str | None = Field(None)
    start_date: datetime = Field(..., alias="startDate")
    end_date: datetime = Field(..., alias="endDate")
    head_pic_url: str | None = Field(None, alias="headPicUrl")


class PersonSearchParams(BaseModel):
    """Parameters for searching persons"""

    page_index: int = Field(1, alias="pageIndex", ge=1)
    page_size: int = Field(20, alias="pageSize", ge=1, le=500)
    filter: dict | None = None


class PersonPhoto(BaseModel):
    """Person photo update model"""

    person_id: str = Field(..., alias="personId")
    photo_data: str = Field(..., alias="photoData")  # Base64 encoded


class PersonCard(BaseModel):
    """Person card model"""

    card_id: str | None = Field(None, alias="cardId")
    card_no: str = Field(..., alias="cardNo", max_length=20)


class PersonFingerprint(BaseModel):
    """Person fingerprint model"""

    finger_id: str | None = Field(None, alias="fingerId")
    name: str = Field(..., max_length=32)
    data: str = Field(..., max_length=1024)


class PersonPinCode(BaseModel):
    """Person PIN code update model"""

    person_id: str = Field(..., alias="personId")
    pin_code: str = Field(..., alias="pinCode", min_length=4, max_length=8)
