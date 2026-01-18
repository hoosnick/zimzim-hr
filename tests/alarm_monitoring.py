import asyncio

from loguru import logger

from apps.hik.client import HikClient
from apps.hik.models.message import MessageBatch
from tests.config import HIK_APP_KEY, HIK_SECRET_KEY, TOKEN_DATA

# Message counter for saving events
message_counter = 0


def handle_message_sync(batch: MessageBatch) -> None:
    """
    Synchronous callback for handling messages

    Args:
        batch: Message batch received from HikCentral
    """
    global message_counter
    message_counter += 1

    logger.info(f"📨 Received message batch #{message_counter}")
    logger.info(f"   Batch ID: {batch.batch_id}")
    logger.info(f"   Remaining in queue: {batch.remaining_number}")

    # Save to file
    with open(f"test_out/event{message_counter}.json", "w", encoding="utf-8") as f:
        f.write(batch.model_dump_json(indent=2))

    logger.info(f"   Saved to test_out/event{message_counter}.json")


async def handle_message_async(batch: MessageBatch) -> None:
    """
    Asynchronous callback for handling messages

    Args:
        batch: Message batch received from HikCentral
    """
    global message_counter
    message_counter += 1

    logger.info(f"📨 Received message batch #{message_counter}")
    logger.info(f"   Batch ID: {batch.batch_id}")
    logger.info(f"   Remaining in queue: {batch.remaining_number}")

    # Save to file (using async I/O if needed)
    with open(f"test_out/event{message_counter}.json", "w", encoding="utf-8") as f:
        f.write(batch.model_dump_json(indent=2))

    logger.info(f"   Saved to test_out/event{message_counter}.json")

    # Example: do async operations here
    # await some_async_operation()


async def monitor_with_integrated_polling(
    client: HikClient,
    duration: int = 60,
    use_async_callback: bool = True,
):
    """
    Monitor alarms using integrated background polling

    Args:
        client: HikClient instance
        duration: Monitoring duration in seconds (0 for infinite)
        use_async_callback: Use async callback (True) or sync callback (False)
    """
    # Choose callback based on preference
    callback = handle_message_async if use_async_callback else handle_message_sync
    callback_type = "async" if use_async_callback else "sync"

    logger.info(f"Starting integrated polling with {callback_type} callback")

    # Start background polling
    await client.start_polling(
        callback=callback,
        interval=0.5,
        auto_confirm=True,
        subscribe_msg_types=None,  # Subscribe to all message types
    )

    logger.info("✓ Background polling active")

    try:
        if duration == 0:
            # Infinite polling - just wait for cancellation
            logger.info("Polling indefinitely (Ctrl+C to stop)...")
            await asyncio.Event().wait()
        else:
            # Poll for specified duration
            logger.info(f"Polling for {duration} seconds...")
            await asyncio.sleep(duration)

    except asyncio.CancelledError:
        logger.info("Monitoring cancelled")
    finally:
        # Stop polling (this will also unsubscribe)
        await client.stop_polling()


async def main():
    """Main function"""

    duration = 0  # Set to 0 for infinite polling
    use_async_callback = True  # Set to False to use sync callback

    async with HikClient(
        app_key=HIK_APP_KEY,
        secret_key=HIK_SECRET_KEY,
        token_data=TOKEN_DATA.model_dump(),
    ) as client:
        if duration == 0:
            print("🔔 Monitoring alarms indefinitely (Ctrl+C to stop)...")
        else:
            print(f"🔔 Monitoring alarms for {duration} seconds...")

        print(f"📡 Using {'async' if use_async_callback else 'sync'} callback")
        print(f"⚙️  Auto-confirm: True, Interval: 0.5s")
        print("-" * 60)

        await monitor_with_integrated_polling(
            client,
            duration=duration,
            use_async_callback=use_async_callback,
        )

        print("-" * 60)
        print(f"✅ Monitoring complete! Processed {message_counter} messages")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Monitoring stopped by user")
