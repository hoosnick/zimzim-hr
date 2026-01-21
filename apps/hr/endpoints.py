from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from loguru import logger

from apps.hik.client import HikClient
from apps.hr.models import (
    CardCollectRequest,
    CardCollectResponse,
    FingerprintCollectRequest,
    FingerprintCollectResponse,
)
from apps.hr.tables import Area, Device, Group, Person
from core.config import settings

router = APIRouter()


@router.post(
    "/persons/collect-fingerprint",
    response_model=FingerprintCollectResponse,
    tags=["Persons"],
)
async def collect_fingerprint(request: FingerprintCollectRequest):
    """
    Collect fingerprint data from a device.

    This operation may take 10-15 seconds as it waits for the device to scan the fingerprint.
    The device must support fingerprint collection and be added to HCC/HCT.

    Returns fingerprint data and quality score (1-100, recommended >80).
    """
    try:
        async with HikClient(
            app_key=settings.HIK.APP_KEY, secret_key=settings.HIK.SECRET_KEY
        ) as client:
            result = await client.collect_person_fingerprint(
                device_serial=request.device_serial
            )

            return FingerprintCollectResponse(
                finger_data=result.finger_data,
                finger_quality=result.finger_quality,
            )

    except Exception as e:
        logger.error(f"Failed to collect fingerprint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect fingerprint: {str(e)}",
        )


@router.post(
    "/persons/collect-card",
    response_model=CardCollectResponse,
    tags=["Persons"],
)
async def collect_card(request: CardCollectRequest):
    """
    Collect card information from a device.

    This operation may take 10-15 seconds as it waits for the device to scan the card.
    The device must support card collection and be added to HCC/HCT.

    Returns the card number.
    """
    try:
        async with HikClient(
            app_key=settings.HIK.APP_KEY, secret_key=settings.HIK.SECRET_KEY
        ) as client:
            result = await client.collect_person_card(
                device_serial=request.device_serial
            )

            return CardCollectResponse(card_no=result.card_no)

    except Exception as e:
        logger.error(f"Failed to collect card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect card: {str(e)}",
        )
