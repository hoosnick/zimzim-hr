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


class PersonCardUpdate(BaseModel):
    """Person card update model for API request"""

    id: str | None = None  # If not provided, adds card; if provided, edits
    card_no: str = Field(
        ..., alias="cardNo", max_length=20
    )  # Card number, cannot be duplicated


class PersonCardsUpdate(BaseModel):
    """Person cards update request model"""

    person_id: str = Field(..., alias="personId")
    card_list: list[PersonCardUpdate] | None = Field(
        None, alias="cardList"
    )  # If None or empty, deletes all cards


class PersonFingerprint(BaseModel):
    """Person fingerprint model"""

    finger_id: str | None = Field(None, alias="fingerId")
    name: str = Field(..., max_length=32)
    data: str = Field(..., max_length=1024)


class PersonFingerprintUpdate(BaseModel):
    """Person fingerprint update model for API request"""

    id: str | None = None  # If not provided, adds fingerprint; if provided, edits
    name: str = Field(..., max_length=32)  # Which finger the fingerprint belongs to
    data: str = Field(..., max_length=1024)  # Hex data


class PersonFingersUpdate(BaseModel):
    """Person fingerprints update request model"""

    person_id: str = Field(..., alias="personId")
    finger_list: list[PersonFingerprintUpdate] | None = Field(
        None, alias="fingerList"
    )  # If None or empty, deletes all fingerprints


class PersonPinCode(BaseModel):
    """Person PIN code update model"""

    person_id: str = Field(..., alias="personId")
    pin_code: str = Field(..., alias="pinCode", min_length=4, max_length=8)


# Response models for update operations


class FingerFailedItem(BaseModel):
    """Failed fingerprint item in update response"""

    id: str
    failed_name: str = Field(..., alias="failedName")
    error_code: str = Field(..., alias="errorCode")


class FingerFailed(BaseModel):
    """Fingerprint update failure information"""

    person_id: str = Field(..., alias="personId")
    person_name: str = Field(..., alias="personName")
    error_code: str = Field(..., alias="errorCode")
    finger_list: list[FingerFailedItem] = Field(
        default_factory=list, alias="fingerList"
    )


class PersonFingersUpdateResponse(BaseModel):
    """Response model for update person fingers"""

    finger_failed: FingerFailed | None = Field(None, alias="fingerFailed")


class CardFailedItem(BaseModel):
    """Failed card item in update response"""

    card_id: str = Field(..., alias="cardId")
    card_no: str = Field(..., alias="cardNo")
    error_code: str = Field(..., alias="errorCode")


class CardFailed(BaseModel):
    """Card update failure information"""

    person_id: str = Field(..., alias="personId")
    person_name: str = Field(..., alias="personName")
    error_code: str = Field(..., alias="errorCode")
    card_list: list[CardFailedItem] = Field(default_factory=list, alias="cardList")


class PersonCardsUpdateResponse(BaseModel):
    """Response model for update person cards"""

    card_failed: CardFailed | None = Field(None, alias="cardFailed")
