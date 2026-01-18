import uuid
from typing import Annotated

import httpx
from faststream import Context, Depends, FastStream
from loguru import logger

from apps.hr.tables import Message
from core.broker import broker, stream
from core.config import settings
from core.db import database_connection

app = FastStream(broker, logger=logger)


class HTTPClientManager:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._is_healthy = True

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed or not self._is_healthy:
            await self._create_client()
        return self._client

    async def _create_client(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(
                max_connections=100, max_keepalive_connections=20, keepalive_expiry=30.0
            ),
            http2=True,  # Enable HTTP/2 for better performance
            follow_redirects=True,
            max_redirects=3,
        )
        self._is_healthy = True
        logger.info("HTTP client created/recreated")

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client closed")

    def mark_unhealthy(self):
        self._is_healthy = False


http_client_manager = HTTPClientManager()


async def get_http_client() -> httpx.AsyncClient:
    return await http_client_manager.get_client()


@app.on_startup
async def on_startup():
    await database_connection()
    await http_client_manager.get_client()  # Pre-warm the client
    logger.info("Worker startup complete")


@app.on_shutdown
async def on_shutdown():
    await database_connection(close=True)
    await http_client_manager.close()
    logger.info("Worker shutdown complete")


@broker.subscriber(stream=stream)
async def handle_event(
    body: dict,
    event_id: Annotated[str, Context("message.headers.event_id")],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
):
    message_id = uuid.UUID(event_id)
    logger.info(f"Processing message {message_id}")

    await Message.update(
        {
            Message.status: Message.Status.processing,
        }
    ).where(Message.id == message_id)

    try:
        response = await client.post(
            settings.HTTP_WEBHOOK_URL,
            json=body,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            await Message.update(
                {
                    Message.status: Message.Status.done,
                }
            ).where(Message.id == message_id)
            logger.info(
                "Message %s delivered successfully to %s"
                % (message_id, settings.HTTP_WEBHOOK_URL)
            )
        else:
            await Message.update(
                {
                    Message.status: Message.Status.failed,
                    Message.last_error: "HTTP %d: %s"
                    % (response.status_code, response.text),
                    Message.retry_count: Message.retry_count + 1,
                }
            ).where(Message.id == message_id)
            logger.error(
                "Message %s failed with status %d" % (message_id, response.status_code)
            )
            raise Exception(f"HTTP {response.status_code}")

    except httpx.ConnectError as e:
        # Network-level failures - mark client as unhealthy
        http_client_manager.mark_unhealthy()
        await Message.update(
            {
                Message.status: Message.Status.failed,
                Message.last_error: f"Connection error: {str(e)}",
                Message.retry_count: Message.retry_count + 1,
            }
        ).where(Message.id == message_id)
        logger.error("Message %s connection error: %s" % (message_id, str(e)))
        raise

    except Exception as e:
        await Message.update(
            {
                Message.status: Message.Status.failed,
                Message.last_error: str(e),
                Message.retry_count: Message.retry_count + 1,
            }
        ).where(Message.id == message_id)
        logger.error("Message %s processing error: %s" % (message_id, str(e)))
        raise


if __name__ == "__main__":
    app.run()
