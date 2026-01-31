import asyncio
import uuid

from loguru import logger
from redis.asyncio import Redis

from apps.hik.client_manager import get_hik_client_manager
from apps.hik.models.message import MessageBatch
from apps.hr.tables import Message
from apps.utils.logger import setup_logger
from core.config import settings
from core.db import database_connection
from core.mq.broker import broker

# Setup poller-specific logging
setup_logger("poller")


async def handle_event(batch: MessageBatch) -> None:
    logger.info(
        "Received batch %s, remaining: %s" % (batch.batch_id, batch.remaining_number)
    )

    message_id = uuid.uuid4()

    message = Message(
        id=message_id,
        payload=batch.model_dump(),
        status=Message.Status.pending,
    )
    await message.save()
    logger.info("Saved message %s to database" % message_id)

    await broker.publish(
        batch.model_dump_json().encode(),
        stream="events",
        headers={"event_id": str(message_id)},
    )
    logger.info("Published message %s to Redis stream" % message_id)


async def main():
    # Initialize database
    await database_connection()

    # Initialize broker
    await broker.connect()

    # Initialize Redis for token caching
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=False,
    )

    # Initialize HikClient Manager (shares tokens with API server)
    manager = await get_hik_client_manager()
    await manager.initialize(redis_client)

    # Get shared client instance
    client = await manager.get_client()

    logger.info("Starting event polling...")

    await client.start_polling(
        callback=handle_event,
        interval=0.5,
        auto_confirm=True,
    )

    logger.info("Polling active, waiting for events...")

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Poller cancelled")
    finally:
        # Cleanup
        await client.stop_polling()
        await manager.shutdown()
        await redis_client.aclose()
        await broker.stop()
        await database_connection(close=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Poller stopped by user")
