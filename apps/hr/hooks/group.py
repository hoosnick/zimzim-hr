from loguru import logger
from starlette.exceptions import HTTPException

from apps.hr.hooks.base import BaseHikHook
from apps.hr.tables import Group


class GroupHook(BaseHikHook):
    """Hook for Group (Person Group) CRUD operations with HikVision API integration"""

    async def pre_save(self, row: Group) -> Group:
        """
        Create person group in HikVision before saving to database.

        Args:
            row: Group row to be created

        Returns:
            Group row with group_id from HikVision API
        """
        try:
            client = await self._get_client()

            # Get area_id if area is set
            area_id = row.area
            row.parent_group_id = None

            # Call HikVision API to create person group
            group_id = await client.add_person_group(
                group_name=row.name,
                description=row.description,
                area_id=area_id,
            )

            # Set the group_id from HikVision API response
            row.group_id = group_id

            logger.info(
                "Created person group in HikVision: %s - %s" % (group_id, row.name)
            )

            return row

        except Exception as e:
            logger.error("Failed to create person group in HikVision: %s" % str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to create person group in HikVision: %s" % str(e),
            )
        finally:
            await self._close_client()

    async def pre_patch(self, row_id: str, values: dict) -> dict:
        """
        Update person group in HikVision before updating database.

        Args:
            row_id: ID of the group to update
            values: Dictionary of fields to update

        Returns:
            Updated values dictionary
        """
        try:
            client = await self._get_client()

            # Call HikVision API to update person group
            await client.update_person_group(
                group_id=row_id,
                group_name=values.get("name"),
                description=values.get("description"),
                parent_id=values.get("parent_group_id"),
                area_id=values.get("area"),
            )

            logger.info(
                "Updated person group in HikVision: %s - %s"
                % (row_id, values.get("name"))
            )

            return values

        except Exception as e:
            logger.error("Failed to update person group in HikVision: %s" % str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to update person group in HikVision: %s" % str(e),
            )
        finally:
            await self._close_client()

    async def pre_delete(self, row_id: str) -> None:
        """
        Delete person group from HikVision before deleting from database.

        Args:
            row_id: ID of the group to delete
        """
        try:
            # Fetch group from database to get group_id

            client = await self._get_client()

            # Call HikVision API to delete person group
            await client.delete_person_group(group_id=row_id)

            logger.info("Deleted person group from HikVision: %s" % row_id)

        except Exception as e:
            logger.error("Failed to delete person group from HikVision: %s" % str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to delete person group from HikVision: %s" % str(e),
            )
        finally:
            await self._close_client()


# Create singleton instance
group_hook = GroupHook()
