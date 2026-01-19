from pydantic import Field

from .common import BaseModel


class DeviceInfo(BaseModel):
    """Device information model"""

    name: str = Field(..., max_length=64)
    serial_number: str = Field(..., alias="ezvizSerialNo", max_length=30)
    verify_code: str = Field(..., alias="ezvizVerifyCode", max_length=30)
    username: str | None = Field(None, max_length=32)
    password: str | None = Field(None, max_length=32)


class DeviceInfo2(BaseModel):
    """Device information"""

    name: str = Field(..., max_length=32)
    id: str = Field(..., max_length=32)
    username: str | None = Field(None, max_length=32)
    password: str | None = Field(None, max_length=16)


class ImportToArea(BaseModel):
    """Import device to area model"""

    enable: int | None = Field(None, ge=0, le=1)
    area_id: str | None = Field(None, alias="areaId", max_length=32)


class TimeZone(BaseModel):
    """Time zone model"""

    id: str = Field(default="100", max_length=8, description="Time zone ID")
    apply_to_device: str = Field(
        ...,
        alias="applyToDevice",
        max_length=1,
        pattern="^[01]$",
        description="Whether to apply to device: 0 (not apply), 1 (apply)",
    )


class DeviceList(BaseModel):
    """List of successfully added devices."""

    alias: str = Field(..., max_length=32)
    device_id: str = Field(..., alias="deviceId", max_length=32)
    device_serial: str = Field(..., alias="deviceSerial", max_length=30)
    error_code: str | None = Field(None, alias="errorCode", max_length=16)


class AddDeviceResponse(BaseModel):
    """Response model for adding devices"""

    task_id: str | None = Field(None, alias="taskId", max_length=256)
    failed: int = Field(..., max_length=16)
    succeeded: int = Field(..., max_length=16)
    total: int = Field(..., max_length=16)
    device_list: list[DeviceList] | None = Field(None, alias="deviceList")


class Device(BaseModel):
    """Device model"""

    id: str = Field(..., max_length=32)
    name: str = Field(..., max_length=64)
    category: str | None = Field(None, max_length=64)
    type: str | None = Field(None, max_length=64)
    serial_number: str | None = Field(None, alias="serialNo", max_length=30)
    version: str | None = Field(None, max_length=32)
    time_zone: str | None = Field(None, alias="timeZone", max_length=8)
    online_status: int | None = Field(None, alias="onlineStatus", ge=0, le=2)
    add_time: str | None = Field(None, alias="addTime", max_length=32)


class GetDevicesResVo(BaseModel):
    """Response model for getting devices"""

    total: int = Field(..., alias="totalCount")
    page_index: int = Field(..., alias="pageIndex")
    page_size: int = Field(..., alias="pageSize", le=500)
    devices: list[Device] = Field(..., alias="device")


class Area(BaseModel):
    """Area information model"""

    id: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=64)


class CameraChannel(BaseModel):
    """Camera channel information model"""

    id: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=64)
    no: str | None = Field(None, max_length=16)
    online: str | None = Field(None, max_length=16)
    area: Area | None = None


class AlarmInputChannel(BaseModel):
    """Alarm input channel information model"""

    id: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=64)
    no: str | None = Field(None, max_length=16)
    online: str | None = Field(None, max_length=16)
    area: Area | None = None


class AlarmOutputChannel(BaseModel):
    """Alarm output channel information model"""

    id: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=64)
    no: str | None = Field(None, max_length=16)
    online: str | None = Field(None, max_length=16)
    area: Area | None = None


class DeviceBaseInfo(BaseModel):
    """Device basic information model"""

    id: str | None = Field(None, max_length=32)
    name: str | None = Field(None, max_length=64)
    category: str | None = Field(None, max_length=64)
    serial_number: str | None = Field(None, alias="serialNo", max_length=30)
    version: str | None = Field(None, max_length=32)
    type: str | None = Field(None, max_length=64)
    stream_encrypt_enable: int | None = Field(
        None, alias="streamEncryptEnable", ge=0, le=1
    )
    available_camera_channel_num: int | None = Field(
        None, alias="availableCameraChannelNum"
    )
    available_alarm_input_channel_num: int | None = Field(
        None, alias="availableAlarmInputChannelNum"
    )
    available_alarm_output_channel_num: int | None = Field(
        None, alias="availableAlarmOutputChannelNum"
    )


class GetDeviceInfo(BaseModel):
    """Get device info response model"""

    base_info: DeviceBaseInfo | None = Field(None, alias="baseInfo")
    camera_channel: list[CameraChannel] | None = Field(None, alias="cameraChannel")
    alarm_input_channel: list[AlarmInputChannel] | None = Field(
        None, alias="alarmInputChannel"
    )
    alarm_output_channel: list[AlarmOutputChannel] | None = Field(
        None, alias="alarmOutputChannel"
    )


class CapturedPic(BaseModel):
    """Captured picture model"""

    capture_url: str = Field(..., alias="captureUrl", max_length=256)
    is_encrypted: int = Field(..., alias="isEncrypted", ge=0, le=1)
