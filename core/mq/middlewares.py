import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Final

from faststream import BaseMiddleware, Logger, StreamMessage
from typing_extensions import override


class RetryMiddleware(BaseMiddleware):
    """Retry middleware with exponential backoff for message processing"""

    MAX_RETRIES: Final[int] = 3

    @override
    async def consume_scope(
        self,
        call_next: Callable[[StreamMessage[Any]], Awaitable[Any]],
        msg: StreamMessage[Any],
    ) -> Any:
        logger_instance: Logger = self.context.get_local("logger")
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return await call_next(msg)
            except Exception as e:
                if attempt == self.MAX_RETRIES:
                    logger_instance.exception(
                        "Failed after %s retries. Marking as failed." % self.MAX_RETRIES
                    )
                    raise

                # Calculate exponential backoff delay
                delay = 2**attempt
                logger_instance.warning(
                    "Attempt %s failed: %s. Retrying in %ss..."
                    % (attempt + 1, str(e), delay)
                )
                await asyncio.sleep(delay)
        return None
