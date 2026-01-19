from abc import ABC, abstractmethod

from loguru import logger
from piccolo.table import Table

from apps.hik.client import HikClient
from core.config import settings


class BaseHikHook(ABC):
    """
    Base abstract class for HikVision API hooks.
    All CRUD operations first call the HikVision API, then proceed to database operations.
    """

    def __init__(self):
        self._client: HikClient | None = None

    async def _get_client(self) -> HikClient:
        """Get or create HikClient instance"""
        if self._client is None:
            self._client = HikClient(
                app_key=settings.HIK.APP_KEY,
                secret_key=settings.HIK.SECRET_KEY,
            )
            await self._client.open()
        return self._client

    async def _close_client(self) -> None:
        """Close HikClient instance"""
        if self._client is not None:
            await self._client.close()
            self._client = None

    @abstractmethod
    async def pre_save(self, row: Table) -> Table:
        """
        Hook called before saving a new row.
        Should call HikVision API to create the resource.

        Args:
            row: The Table row to be saved

        Returns:
            Modified row with HikVision API response data
        """
        pass

    @abstractmethod
    async def pre_patch(self, row_id: int, values: dict) -> dict:
        """
        Hook called before patching an existing row.
        Should call HikVision API to update the resource.

        Args:
            row_id: ID of the row to be updated
            values: Dictionary of fields to update

        Returns:
            Modified values dictionary
        """
        pass

    @abstractmethod
    async def pre_delete(self, row_id: int) -> None:
        """
        Hook called before deleting a row.
        Should call HikVision API to delete the resource.

        Args:
            row_id: ID of the row to be deleted
        """
        pass
