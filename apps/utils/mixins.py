import datetime

from piccolo.columns.column_types import Timestamptz


class UpdatesMixin:
    created_at = Timestamptz()
    updated_at = Timestamptz(
        auto_update=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


def start_date_default():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now


def end_date_default():
    now = datetime.datetime.now(datetime.timezone.utc)
    end = now + datetime.timedelta(days=365 * 10)  # 10 years ahead
    return end
