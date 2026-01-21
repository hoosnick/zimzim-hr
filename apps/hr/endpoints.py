from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from apps.hik.client import HikClient
from apps.hik.client_manager import get_hik_client, get_hik_client_manager
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
async def collect_fingerprint(
    request: FingerprintCollectRequest,
    client: HikClient = Depends(get_hik_client),
):
    """
    Collect fingerprint data from a device.

    This operation may take 10-15 seconds as it waits for the device to scan the fingerprint.
    The device must support fingerprint collection and be added to HCC/HCT.

    Returns fingerprint data and quality score (1-100, recommended >80).
    """
    try:
        result = await client.collect_person_fingerprint(
            device_serial=request.device_serial
        )

        return FingerprintCollectResponse(
            finger_data=result.finger_data,
            finger_quality=result.finger_quality,
        )

    except Exception as e:
        logger.error("Failed to collect fingerprint: %s" % str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect fingerprint: %s" % str(e),
        )


@router.post(
    "/persons/collect-card",
    response_model=CardCollectResponse,
    tags=["Persons"],
)
async def collect_card(
    request: CardCollectRequest,
    client: HikClient = Depends(get_hik_client),
):
    """
    Collect card information from a device.

    This operation may take 10-15 seconds as it waits for the device to scan the card.
    The device must support card collection and be added to HCC/HCT.

    Returns the card number.
    """
    try:
        result = await client.collect_person_card(device_serial=request.device_serial)

        return CardCollectResponse(card_no=result.card_no)

    except Exception as e:
        logger.error("Failed to collect card: %s" % str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect card: %s" % str(e),
        )


@router.post("/admin/refresh-token", tags=["Admin"])
async def refresh_hikvision_token():
    """
    Manually refresh the HikVision API token.

    Useful for:
    - Testing token refresh mechanism
    - Recovering from token issues
    - Force token refresh without waiting for expiry

    Returns the new token data (without exposing the actual token).
    """
    try:
        manager = await get_hik_client_manager()

        if not manager.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="HikClient manager not initialized",
            )

        token_data = await manager.refresh_token()

        # Return safe token info (without actual token value)
        return JSONResponse(
            content={
                "success": True,
                "message": "Token refreshed successfully",
                "user_id": token_data.get("user_id"),
                "expire_time": token_data.get("expire_time"),
                "expires_in_hours": (
                    (token_data.get("expire_time", 0) - int(datetime.now().timestamp()))
                    / 3600
                ),
            }
        )

    except Exception as e:
        logger.error("Failed to refresh token: %s" % str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token: %s" % str(e),
        )


@router.get("/admin/token-status", tags=["Admin"])
async def get_token_status():
    """
    Get current HikVision API token status.

    Returns information about the current token without exposing sensitive data.
    """
    try:
        manager = await get_hik_client_manager()

        if not manager.is_initialized:
            return JSONResponse(
                content={
                    "initialized": False,
                    "message": "HikClient manager not initialized",
                }
            )

        # Access token manager through the client manager
        if manager._token_manager:
            token_data = await manager._token_manager.get_token_data()

            if token_data:
                current_time = int(datetime.now().timestamp())
                expire_time = token_data.get("expire_time", 0)
                time_remaining = expire_time - current_time

                return JSONResponse(
                    content={
                        "initialized": True,
                        "has_token": True,
                        "user_id": token_data.get("user_id"),
                        "expire_time": expire_time,
                        "time_remaining_seconds": time_remaining,
                        "time_remaining_hours": time_remaining / 3600,
                        "is_expired": time_remaining <= 0,
                    }
                )

        return JSONResponse(
            content={
                "initialized": True,
                "has_token": False,
                "message": "No token available",
            }
        )

    except Exception as e:
        logger.error("Failed to get token status: %s" % str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get token status: %s" % str(e),
        )
