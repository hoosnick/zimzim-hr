import datetime

from piccolo.columns.column_types import Timestamp


class UpdatesMixin:
    created_at = Timestamp()
    updated_at = Timestamp(auto_update=datetime.datetime.now)


def start_date_default():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now


def end_date_default():
    now = datetime.datetime.now(datetime.timezone.utc)
    end = now + datetime.timedelta(days=365 * 10)  # 10 years ahead
    return end
