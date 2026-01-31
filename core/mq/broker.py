from faststream.redis import RedisBroker, StreamSub

from core.config import settings
from core.mq.middlewares import RetryMiddleware

broker = RedisBroker(
    url=settings.REDIS_URL,
    middlewares=[RetryMiddleware],
)

stream = StreamSub(
    "events",
    group="workers",
    consumer="worker-{id}",
    polling_interval=5000,
)
