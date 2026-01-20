from loguru import logger
from starlette.exceptions import HTTPException

from apps.hik.models.device import DeviceInfo, DeviceInfo2, ImportToArea, TimeZone
from apps.hr.hooks.base import BaseHikHook
from apps.hr.tables import Device


class DeviceHook(BaseHikHook):
    """Hook for Device CRUD operations with HikVision API integration"""

    async def pre_save(self, row: Device) -> Device:
        """
        Add device to HikVision before saving to database.

        Args:
            row: Device row to be created

        Returns:
            Device row with device_id from HikVision API
        """
        try:
            client = await self._get_client()

            # Prepare device info for HikVision API
            device_info = DeviceInfo(
                name=row.name,
                serial_number=row.serial_no,
                verify_code=row.verify_code,
                username=row.username,
                password=row.password,
            )

            # Prepare timezone
            timezone = TimeZone(
                id="100",  # Default timezone in future, make configurable if needed
                apply_to_device="1",
            )

            if row.area:
                import_to_area = ImportToArea(area_id=row.area, enable=1)

            # Call HikVision API to add device
            response = await client.add_device(
                device_info=device_info,
                timezone=timezone,
                device_category=row.category,
                import_to_area=None if not row.area else import_to_area,
            )

            # Get device_id from response
            if response.device_list and len(response.device_list) > 0:
                device_id = response.device_list[0].device_id
                row.device_id = device_id
                logger.info(
                    "Added device to HikVision: %s - %s (%s)"
                    % (device_id, row.name, row.serial_no)
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get device_id from HikVision API response",
                )

            return row

        except Exception as e:
            logger.error("Failed to add device to HikVision: %s" % e)
            raise HTTPException(
                status_code=500,
                detail="Failed to add device to HikVision: %s" % e,
            )
        finally:
            await self._close_client()

    async def pre_patch(self, row_id: str, values: dict) -> dict:
        """
        Update device in HikVision before updating database.

        Args:
            row_id: ID of the device to update
            values: Dictionary of fields to update

        Returns:
            Updated values dictionary
        """
        try:
            # Fetch current device from database to get device_id
            current_device = await Device.objects().get(Device.id == row_id)

            if current_device is None:
                raise HTTPException(
                    status_code=404,
                    detail="Device with id %s not found" % row_id,
                )

            client = await self._get_client()

            # Prepare device info for update
            device_info = DeviceInfo2(
                id=row_id,
                name=values.get("name"),
                username=values.get("username"),
                password=values.get("password"),
            )

            # Prepare timezone (optional for update)
            timezone = TimeZone(
                id="100",
                apply_to_device="1",
            )

            # compare with existing values to avoid sending not changed fields
            if (
                values.get("name") == current_device.name
                and values.get("username") == current_device.username
                and values.get("password") == current_device.password
            ):
                logger.info(
                    "No changes detected for device %s. Skipping update."
                    % current_device.device_id
                )
                return values

            # Call HikVision API to update device
            await client.update_device(
                device_info=device_info,
                timezone=timezone,
            )

            logger.info(
                "Updated device in HikVision: %s - %s"
                % (current_device.device_id, device_info.name)
            )

            return values

        except Exception as e:
            logger.error("Failed to update device in HikVision: %s" % e)
            raise HTTPException(
                status_code=500,
                detail="Failed to update device in HikVision: %s" % e,
            )
        finally:
            await self._close_client()

    async def pre_delete(self, row_id: str) -> None:
        """
        Delete device from HikVision before deleting from database.

        Args:
            row_id: ID of the device to delete
        """
        try:
            client = await self._get_client()

            # Call HikVision API to delete device
            await client.delete_device(device_ids=[row_id])

            logger.info("Deleted device from HikVision: %s" % (row_id))

        except Exception as e:
            logger.error("Failed to delete device from HikVision: %s" % e)
            raise HTTPException(
                status_code=500,
                detail="Failed to delete device from HikVision: %s" % e,
            )
        finally:
            await self._close_client()


# Create singleton instance
device_hook = DeviceHook()
