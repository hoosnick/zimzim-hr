from faststream.redis import RedisBroker, StreamSub

from core.config import settings

broker = RedisBroker(url=settings.REDIS_URL)

stream = StreamSub(
    "events",
    group="workers",
    consumer="worker-{id}",
    polling_interval=5000,
)
