from abc import ABC, abstractmethod

from loguru import logger
from piccolo.table import Table

from apps.hik.client import HikClient
from apps.hik.client_manager import get_hik_client_manager


class BaseHikHook(ABC):
    """
    Base abstract class for HikVision API hooks.
    All CRUD operations first call the HikVision API, then proceed to database operations.

    Uses shared HikClient instance via HikClientManager for better performance
    and resource management.
    """

    def __init__(self):
        # No longer storing client instance - using shared manager
        pass

    async def _get_client(self) -> HikClient:
        """Get shared HikClient instance from manager"""
        manager = await get_hik_client_manager()
        return await manager.get_client()

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
