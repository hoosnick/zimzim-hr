import asyncio
from typing import Any, Awaitable, Callable, Literal, Optional

import httpx
from loguru import logger
from pydantic import ValidationError

from core.config import settings

from .exceptions import APIError, AuthenticationError, NetworkError
from .models.auth import TokenRequest, TokenResponse
from .models.message import MessageBatch, MessageSubscription
from .models.person import (
    Person,
    PersonGroup,
    PersonPhoto,
    PersonPinCode,
    PersonSearchParams,
)
from .utils import deserialize_json, is_token_expired, serialize_json

ServerRegion = Literal[
    "russia",
    "singapore",
    "india",
    "europe",
    "south_america",
    "north_america",
    "singapore_team",
]


class HikClient:
    def __init__(
        self,
        app_key: str,
        secret_key: str,
        token_data: Optional[dict[str, Any]] = None,
        region: ServerRegion = "singapore_team",
        timeout: float = settings.HIK.DEFAULT_TIMEOUT,
        connect_timeout: float = settings.HIK.DEFAULT_CONNECT_TIMEOUT,
        max_retries: int = settings.HIK.MAX_RETRIES,
    ):
        self.app_key = app_key
        self.secret_key = secret_key

        self.token_data = token_data or {}

        self.base_url = settings.HIK.SERVERS[region]

        self.timeout = httpx.Timeout(timeout, connect=connect_timeout)
        self.max_retries = max_retries

        self._client: httpx.AsyncClient | None = None

        self._token: Optional[str] = self.token_data.get("access_token")
        self._token_expire_time: Optional[int] = self.token_data.get(
            "expire_time"
        )  # Token expiration timestamp int
        self._user_id: Optional[str] = self.token_data.get("user_id")

        # Polling state
        self._polling_active = False
        self._stop_signal: asyncio.Event | None = None
        self._message_tasks: set[asyncio.Task[Any]] = set()

    async def __aenter__(self) -> "HikClient":
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def open(self) -> None:
        if self._client is not None:
            logger.warning("Client already opened")
            return

        # Create HTTP client with orjson for JSON serialization
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            http2=True,
        )

        # Authenticate and get token
        await self._authenticate()
        logger.info("HikClient session opened successfully")

    async def close(self) -> None:
        # Stop polling if active
        if self._polling_active:
            await self.stop_polling()

        if self._client is not None:
            await self._client.aclose()
            self._client = None
        logger.info("HikClient session closed")

    async def _authenticate(self, expired: bool = False) -> None:
        if self._client is None:
            raise RuntimeError("Client not opened. Use 'async with' or call open()")

        if self.token_data.get("access_token") and not expired:
            self._token = self.token_data["access_token"]
            self._token_expire_time = self.token_data.get("expire_time")
            self._user_id = self.token_data.get("user_id")
        else:
            token_request = TokenRequest(
                app_key=self.app_key, secret_key=self.secret_key
            )

            try:
                response = await self._client.post(
                    f"{self.base_url}/api/hccgw/platform/v1/token/get",
                    content=serialize_json(token_request.model_dump(by_alias=True)),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                data = deserialize_json(response.content)

                if data.get("errorCode") != "0":
                    raise AuthenticationError(
                        data.get("message", "Authentication failed"),
                        error_code=data.get("errorCode"),
                    )

                token_data = TokenResponse(**data["data"])

                self._token = token_data.access_token
                self._token_expire_time = token_data.expire_time
                self._user_id = token_data.user_id

                self.token_data = {
                    "access_token": self._token,
                    "expire_time": self._token_expire_time,
                    "user_id": self._user_id,
                }
                with open("test_out/last_auth.json", "w", encoding="utf-8") as f:
                    f.write(response.text)
            except httpx.HTTPStatusError as e:
                raise AuthenticationError(f"HTTP error during authentication: {e}")
            except httpx.RequestError as e:
                raise NetworkError(f"Network error during authentication: {e}")
            except ValidationError as e:
                raise AuthenticationError(f"Invalid token response format: {e}")

        logger.info(f"Authentication successful. User ID: {self._user_id}")
        logger.info(f"Token: {self._token}")
        logger.info(f"Token expires at: {self._token_expire_time}")

    async def _ensure_token_valid(self) -> None:
        if self._token_expire_time is None:
            await self._authenticate(expired=True)
            return

        if is_token_expired(self._token_expire_time):
            await self._authenticate(expired=True)

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("Client not opened. Use 'async with' or call open()")

        await self._ensure_token_valid()

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Token": self._token or "",
        }

        content = serialize_json(data) if data else None

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    content=content,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()

                result = deserialize_json(response.content)

                # DEBUG: Save last response to file
                with open("test_out/last_response.json", "w", encoding="utf-8") as f:
                    f.write(response.text)

                if result.get("errorCode") == "0":
                    return result

                error_code = result.get("errorCode")
                if error_code == "OPEN000006":
                    # Token expired, re-authenticate and retry
                    logger.warning("Token expired during request, re-authenticating...")
                    await self._authenticate(expired=True)
                    return await self._request(method, endpoint, data, params)

                raise APIError(
                    message=result.get("message", "API request failed"),
                    error_code=error_code,
                    status_code=response.status_code,
                )

            except httpx.HTTPStatusError as e:
                last_exception = APIError(
                    message=f"HTTP error: {e}",
                    status_code=e.response.status_code,
                )
                # Don't retry on client errors (4xx) except 429
                if (
                    400 <= e.response.status_code < 500
                    and e.response.status_code != 429
                ):
                    raise last_exception

            except httpx.RequestError as e:
                last_exception = NetworkError(f"Network error: {e}")

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                backoff_time = settings.HIK.RETRY_BACKOFF_FACTOR * (2**attempt)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {backoff_time:.2f}s..."
                )
                await asyncio.sleep(backoff_time)

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise NetworkError("Request failed after all retries")

    # ========== Device Management APIs ==========

    # ========== Person Management APIs ==========

    async def add_person_group(
        self,
        group_name: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Add a new person group (department)

        Args:
            group_name: Name of the person group
            description: Description of the group (optional)

        Returns:
            Group ID of the created person group
        """
        data = {
            "groupName": group_name,
        }
        if description:
            data["description"] = description

        result = await self._request(
            "POST",
            "/api/hccgw/person/v1/groups/add",
            data=data,
        )

        return result["data"]["groupId"]

    async def get_person_groups(
        self,
        parent_group_id: str = "",
        group_name: str = "",
    ) -> list[PersonGroup]:
        """
        Get person groups (departments)

        Args:
            parent_group_id: Parent group ID (optional)
            group_name: Group name for fuzzy search (optional)

        Returns:
            List of PersonGroup objects
        """
        data = {}
        data["parentGroupId"] = parent_group_id
        data["groupName"] = group_name

        result = await self._request(
            "POST",
            "/api/hccgw/person/v1/groups/search",
            data=data,
        )

        return [
            PersonGroup(**group)
            for group in result.get("data", {}).get("personGroupList", [])
        ]

    async def get_persons(
        self,
        page_index: int = 1,
        page_size: int = 20,
        name_filter: str | None = None,
    ) -> list[Person]:
        """
        Search for persons

        Args:
            page_index: Page number (starting from 1)
            page_size: Items per page (max 500)
            name_filter: Name filter for fuzzy search

        Returns:
            List of Person objects
        """
        search_params = PersonSearchParams(
            page_index=page_index,
            page_size=page_size,
            filter={"name": name_filter} if name_filter else None,
        )

        result = await self._request(
            "POST",
            "/api/hccgw/person/v1/persons/list",
            data=search_params.model_dump(by_alias=True, exclude_none=True),
        )

        person_list = result.get("data", {}).get("personList", [])
        return [Person(**item["personInfo"]) for item in person_list]

    async def add_person(self, person: Person) -> str:
        """
        Add a new person

        Args:
            person: Person object

        Returns:
            Person ID of the created person
        """
        result = await self._request(
            "POST",
            "/api/hccgw/person/v1/persons/add",
            data=person.model_dump(
                by_alias=True, exclude={"person_id", "head_pic_url"}
            ),
        )

        return result["data"]["personId"]

    async def update_person_photo(self, person_id: str, photo_base64: str) -> None:
        """
        Update person's face photo

        Args:
            person_id: Person ID
            photo_base64: Photo data encoded in Base64
        """
        photo = PersonPhoto(person_id=person_id, photo_data=photo_base64)

        await self._request(
            "POST",
            "/api/hccgw/person/v1/persons/photo",
            data=photo.model_dump(by_alias=True),
        )

    async def update_person_pincode(self, person_id: str, pin_code: str) -> None:
        """
        Update person's PIN code

        Args:
            person_id: Person ID
            pin_code: PIN code (4-8 digits)
        """
        pincode = PersonPinCode(person_id=person_id, pin_code=pin_code)

        await self._request(
            "POST",
            "/api/hccgw/person/v1/persons/updatepincode",
            data=pincode.model_dump(by_alias=True),
        )

    async def delete_person(self, person_id: str) -> None:
        """
        Delete a person

        Args:
            person_id: Person ID
        """
        await self._request(
            "POST",
            "/api/hccgw/person/v1/persons/delete",
            data={"personId": person_id},
        )

    # ========== Message APIs ==========

    async def subscribe_messages(
        self,
        subscribe: bool = True,
        msg_types: list[str] = [],
    ) -> None:
        """
        Subscribe to or unsubscribe from alarms

        Args:
            subscribe: True to subscribe, False to unsubscribe
            msg_types: List of message type codes (empty for all messages)
        """
        subscription = MessageSubscription(
            subscribe_type=1 if subscribe else 0,
            msg_type=msg_types,
        )

        await self._request(
            "POST",
            "/api/hccgw/rawmsg/v1/mq/subscribe",
            data=subscription.model_dump(by_alias=True, exclude_none=True),
        )

    async def get_messages(self) -> MessageBatch | None:
        """
        Get messages from queue

        Returns:
            MessageBatch object or None if no messages
        """

        result = await self._request(
            "POST",
            "/api/hccgw/rawmsg/v1/mq/messages",
        )

        batch_data = result.get("data")
        if not batch_data:
            return None

        return MessageBatch(**batch_data)

    async def confirm_messages(self, batch_id: str) -> None:
        """
        Confirm alarm messages have been received

        Args:
            batch_id: Batch ID from get_alarm_messages()
        """
        await self._request(
            "POST",
            "/api/hccgw/rawmsg/v1/mq/messages/complete",
            data={"batchId": batch_id},
        )

    async def start_polling(
        self,
        callback: (
            Callable[[MessageBatch], Any] | Callable[[MessageBatch], Awaitable[Any]]
        ),
        interval: float = 0.5,
        auto_confirm: bool = True,
        subscribe_msg_types: list[str] | None = None,
    ) -> None:
        """
        Start polling for messages in the background

        Args:
            callback: Callback function to handle received messages (sync or async)
            interval: Polling interval in seconds (default: 0.5)
            auto_confirm: Automatically confirm messages after callback (default: True)
            subscribe_msg_types: Message types to subscribe to (None for all)

        Raises:
            RuntimeError: If polling is already active
        """
        if self._polling_active:
            raise RuntimeError("Polling is already active")

        if self._client is None:
            raise RuntimeError("Client not opened. Use 'async with' or call open()")

        logger.info("Starting message polling...")

        # Subscribe to messages
        await self.subscribe_messages(
            subscribe=True,
            msg_types=subscribe_msg_types or [],
        )

        # Initialize stop signal
        self._stop_signal = asyncio.Event()
        self._polling_active = True

        # Create and start polling task
        task = asyncio.create_task(self._polling_loop(callback, interval, auto_confirm))
        self._message_tasks.add(task)
        task.add_done_callback(self._message_tasks.discard)

        logger.info(
            f"Polling started (interval: {interval}s, auto_confirm: {auto_confirm})"
        )

    async def stop_polling(self) -> None:
        """
        Stop the background polling

        Waits for all polling tasks to complete gracefully
        """
        if not self._polling_active:
            logger.warning("Polling is not active")
            return

        logger.info("Stopping message polling...")
        self._polling_active = False

        if self._stop_signal:
            self._stop_signal.set()

        # Wait for all tasks to complete
        if self._message_tasks:
            await asyncio.gather(*self._message_tasks, return_exceptions=True)

        # Unsubscribe from messages
        try:
            await self.subscribe_messages(subscribe=False)
        except Exception as e:
            logger.warning(f"Failed to unsubscribe: {e}")

        logger.info("Polling stopped")

    async def _polling_loop(
        self,
        callback: (
            Callable[[MessageBatch], Any] | Callable[[MessageBatch], Awaitable[Any]]
        ),
        interval: float,
        auto_confirm: bool,
    ) -> None:
        """
        Internal polling loop that fetches and processes messages

        Args:
            callback: Callback function to handle messages
            interval: Polling interval in seconds
            auto_confirm: Whether to auto-confirm messages
        """
        logger.debug("Polling loop started")

        try:
            while self._polling_active and not (
                self._stop_signal and self._stop_signal.is_set()
            ):
                try:
                    # Fetch messages
                    batch = await self.get_messages()

                    if batch and batch.batch_id and batch.batch_id != "0":
                        # Call the callback (handle both sync and async)
                        if asyncio.iscoroutinefunction(callback):
                            await callback(batch)
                        else:
                            # Run sync callback in executor to avoid blocking
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, callback, batch)

                        # Auto-confirm if enabled
                        if auto_confirm:
                            await self.confirm_messages(batch.batch_id)
                            logger.debug(f"Auto-confirmed batch: {batch.batch_id}")

                except asyncio.CancelledError:
                    logger.debug("Polling loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}", exc_info=True)

                # Wait for next poll
                try:
                    await asyncio.wait_for(
                        (
                            self._stop_signal.wait()
                            if self._stop_signal
                            else asyncio.sleep(interval)
                        ),
                        timeout=interval,
                    )
                    if self._stop_signal and self._stop_signal.is_set():
                        break
                except asyncio.TimeoutError:
                    pass  # Normal timeout, continue polling

        except Exception as e:
            logger.error(f"Fatal error in polling loop: {e}", exc_info=True)
        finally:
            logger.debug("Polling loop ended")

    # ========== Utility Methods ==========

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def token_expires_at(self) -> int | None:
        return self._token_expire_time
