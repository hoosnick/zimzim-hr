from enum import Enum

from piccolo.columns import JSONB, UUID, ForeignKey, Integer, Text, Timestamptz, Varchar
from piccolo.columns.readable import Readable
from piccolo.table import Table

from apps.utils.mixins import UpdatesMixin, end_date_default, start_date_default


class Area(UpdatesMixin, Table):
    name = Varchar(null=False)
    area_id = Varchar(length=36, primary_key=True, null=False, index=True)
    parent_area_id = Varchar(length=36, null=False, index=True)

    @classmethod
    def get_readable(cls):
        return Readable("%s [%s]", [cls.name, cls.area_id])


class Device(UpdatesMixin, Table):
    class Category(str, Enum):
        alarmDevice = "alarmDevice"
        encodingDevice = "encodingDevice"
        mobileDevice = "mobileDevice"
        accessControllerDevice = "accessControllerDevice"
        videoIntercomDevice = "videoIntercomDevice"

    device_id = Varchar(
        length=36,
        primary_key=True,
        unique=True,
        null=False,
        index=True,
    )
    name = Varchar(null=False)
    category = Varchar(
        length=22,
        choices=Category,
        default=Category.accessControllerDevice,
        null=False,
        index=True,
    )
    serial_no = Varchar(length=64, unique=True, null=False, index=True)

    verify_code = Varchar(length=64, null=True)
    username = Varchar(length=64, null=True)
    password = Varchar(length=64, null=True)

    area = ForeignKey(references=Area, null=True, index=True)

    @classmethod
    def get_readable(cls):
        return Readable("%s [%s]", [cls.name, cls.serial_no])


class Group(UpdatesMixin, Table):
    group_id = Varchar(
        length=100,
        primary_key=True,
        unique=True,
        null=False,
        index=True,
    )
    parent_group_id = Varchar(length=100, null=True, index=True)
    name = Varchar(length=100, null=False)
    description = Text(null=True)
    area = ForeignKey(references=Area, null=False, index=True)

    @classmethod
    def get_readable(cls):
        return Readable(
            "%s [%s] - %s [%s]",
            [cls.name, cls.group_id, cls.area._.name, cls.area._.area_id],
        )


class Person(UpdatesMixin, Table):
    person_id = Varchar(
        length=36,
        primary_key=True,
        unique=True,
        null=False,
        index=True,
    )
    code = Varchar(length=16, unique=True, null=False, index=True)
    first_name = Varchar(null=False)
    last_name = Varchar(null=False)

    start_date = Timestamptz(default=start_date_default, null=False)
    end_date = Timestamptz(default=end_date_default, null=False)

    finger_data = Text(null=True)  # Base64 encoded fingerprint data
    card_no = Varchar(length=20, null=True, index=True)
    pin_code = Varchar(length=8, null=True)
    face_data = Text(null=True)  # Base64 encoded face data

    group = ForeignKey(references=Group, null=False, index=True)

    @classmethod
    def get_readable(cls):
        return Readable("%s %s [%s]", [cls.first_name, cls.last_name, cls.code])


class Message(UpdatesMixin, Table):
    class Status(str, Enum):
        pending = "pending"
        published = "published"
        processing = "processing"
        failed = "failed"
        done = "done"

    id = UUID(
        unique=True,
        null=False,
        primary_key=True,
        index=True,
    )
    payload = JSONB(null=False)
    status = Varchar(
        length=10,
        choices=Status,
        default=Status.pending,
        null=False,
        index=True,
    )
    retry_count = Integer(null=False, default=0)
    last_error = Text(null=True)

    @classmethod
    def get_readable(cls):
        return Readable("%s - %s", [cls.id, cls.status])
