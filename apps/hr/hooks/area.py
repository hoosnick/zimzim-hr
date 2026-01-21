from loguru import logger
from starlette.exceptions import HTTPException

from apps.hr.hooks.base import BaseHikHook
from apps.hr.tables import Area


class AreaHook(BaseHikHook):
    """Hook for Area CRUD operations with HikVision API integration"""

    async def pre_save(self, row: Area) -> Area:
        """
        Create area in HikVision before saving to database.

        Args:
            row: Area row to be created

        Returns:
            Area row with area_id from HikVision API
        """
        try:
            client = await self._get_client()

            # Call HikVision API to create area
            area_id = await client.add_area(
                area_name=row.name,
                parent_area_id="-1" if not row.parent_area_id else row.parent_area_id,
            )

            # Set the area_id from HikVision API response
            row.area_id = area_id

            logger.info("Created area in HikVision: %s - %s" % (area_id, row.name))

            return row

        except Exception as e:
            logger.error("Failed to create area in HikVision: %s" % str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to create area in HikVision: %s" % str(e),
            )

    async def pre_patch(self, row_id: str, values: dict) -> dict:
        """
        Update area in HikVision before updating database.

        Args:
            row_id: ID of the area to update
            values: Dictionary of fields to update

        Returns:
            Updated values dictionary
        """
        raise HTTPException(
            status_code=400, detail="HikVision API does not support area updates"
        )

    async def pre_delete(self, row_id: str) -> None:
        """
        Delete area from HikVision before deleting from database.

        Args:
            row_id: ID of the area to delete
        """
        raise HTTPException(
            status_code=400, detail="HikVision API does not support area deletions"
        )


# Create singleton instance
area_hook = AreaHook()
