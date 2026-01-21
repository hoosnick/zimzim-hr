from pydantic import BaseModel, Field


class FingerprintCollectRequest(BaseModel):
    device_serial: str = Field(...)


class FingerprintCollectResponse(BaseModel):
    finger_data: str | None = Field(None)
    finger_quality: int | None = Field(None)


class CardCollectRequest(BaseModel):
    device_serial: str = Field(...)


class CardCollectResponse(BaseModel):
    card_no: str | None = Field(None)
