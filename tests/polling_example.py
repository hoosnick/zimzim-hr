import asyncio

from loguru import logger

from apps.hik.client import HikClient
from apps.hik.models.message import MessageBatch
from tests.config import TOKEN_DATA

# ========== APPROACH 1: Integrated Background Polling (Recommended) ==========


async def message_handler(batch: MessageBatch) -> None:
    """Handle received messages"""
    logger.info(f"📨 Message received: Batch ID {batch.batch_id}")
    logger.info(f"   Remaining: {batch.remaining_number}")
    # Process your message here


async def integrated_polling_example():
    """Example using integrated background polling"""
    async with HikClient(token_data=TOKEN_DATA.model_dump()) as client:
        # Start polling in background
        await client.start_polling(
            callback=message_handler,  # Your callback (sync or async)
            interval=0.5,  # Poll every 500ms
            auto_confirm=True,  # Auto-confirm messages
            subscribe_msg_types=None,  # All message types
        )

        # Do other work while polling happens in background
        logger.info("Polling in background, doing other work...")
        await asyncio.sleep(60)  # Poll for 60 seconds

        # Polling stops automatically when client closes


# ========== APPROACH 2: Manual Polling (More Control) ==========


async def manual_polling_example():
    """Example using manual polling loop"""
    async with HikClient(token_data=TOKEN_DATA.model_dump()) as client:
        # Subscribe manually
        await client.subscribe_messages(subscribe=True)

        # Manual polling loop
        for _ in range(120):  # Poll 120 times (60 seconds at 0.5s interval)
            batch = await client.get_messages()

            if batch and batch.batch_id and batch.batch_id != "0":
                logger.info(f"📨 Message received: Batch ID {batch.batch_id}")
                # Process your message here
                await client.confirm_messages(batch.batch_id)

            await asyncio.sleep(0.5)

        # Unsubscribe manually
        await client.subscribe_messages(subscribe=False)


# ========== Main ==========


async def main():
    print("Choose polling approach:")
    print("1. Integrated background polling (recommended)")
    print("2. Manual polling loop")

    # Uncomment the one you want to use:
    await integrated_polling_example()
    # await manual_polling_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Stopped by user")
