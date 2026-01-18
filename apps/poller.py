import asyncio
import uuid

from loguru import logger

from apps.hik.client import HikClient
from apps.hik.models.message import MessageBatch
from apps.hr.tables import Message
from core.broker import broker
from core.config import settings
from core.db import database_connection


async def handle_event(batch: MessageBatch) -> None:
    logger.info(f"Received batch {batch.batch_id}, remaining: {batch.remaining_number}")

    message_id = uuid.uuid4()

    message = Message(
        id=message_id,
        payload=batch.model_dump(),
        status=Message.Status.pending,
    )
    await message.save()
    logger.info(f"Saved message {message_id} to database")

    await broker.publish(
        batch.model_dump_json().encode(),
        stream="events",
        headers={"event_id": str(message_id)},
    )
    logger.info(f"Published message {message_id} to Redis stream")


async def main():
    await database_connection()
    await broker.connect()

    async with HikClient(
        app_key=settings.HIK.APP_KEY,
        secret_key=settings.HIK.SECRET_KEY,
    ) as client:
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
            await client.stop_polling()
            await broker.stop()
            await database_connection(close=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Poller stopped by user")
