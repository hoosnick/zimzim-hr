from typing import Any

from pydantic import Field

from .common import BaseModel


class MessageSubscription(BaseModel):
    """Message subscription model"""

    subscribe_type: int = Field(..., alias="subscribeType")  # 0=cancel, 1=subscribe
    msg_type: list[str] | None = Field(..., alias="msgType")


class MessageBatch(BaseModel):
    """Message batch response"""

    batch_id: str = Field(..., alias="batchId")
    remaining_number: int = Field(..., alias="remainingNumber")
    event: list[dict[str, Any]] | None = None
