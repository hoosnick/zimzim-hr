"""
HikClient Manager for application-level lifecycle management.

Provides a singleton HikClient instance with proper startup/shutdown
handling and token management integration.
"""

import asyncio
from typing import Any, Optional

from loguru import logger
from redis.asyncio import Redis

from apps.hik.client import HikClient
from apps.hik.token_manager import TokenManager
from core.config import settings


class HikClientManager:
    """
    Application-level HikClient manager with singleton pattern.

    Features:
    - Single long-lived HikClient instance per application
    - Integrated with TokenManager for token persistence
    - Proper lifecycle management (startup/shutdown)
    - Thread-safe client access
    - Automatic token refresh and persistence
    """

    def __init__(self):
        self._client: Optional[HikClient] = None
        self._token_manager: Optional[TokenManager] = None
        self._redis: Optional[Redis] = None
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self, redis_client: Redis) -> None:
        """
        Initialize the client manager.

        Args:
            redis_client: Redis client for token caching

        Should be called during application startup.
        """
        async with self._lock:
            if self._initialized:
                logger.warning("HikClientManager already initialized")
                return

            self._redis = redis_client

            # Create token manager
            self._token_manager = TokenManager(
                redis_client=redis_client,
                app_key=settings.HIK.APP_KEY,
                secret_key=settings.HIK.SECRET_KEY,
            )

            # Try to get existing token from cache
            token_data = await self._token_manager.get_token_data()

            # Create HikClient instance
            self._client = HikClient(
                app_key=settings.HIK.APP_KEY,
                secret_key=settings.HIK.SECRET_KEY,
                token_data=token_data,  # Reuse cached token if available
                region="singapore_team",
            )

            # Open the client session
            await self._client.open()

            # Save the new token to cache (in case it was refreshed)
            if self._client.token_data:
                await self._token_manager.save_token_data(self._client.token_data)

            self._initialized = True
            logger.info("HikClientManager initialized successfully")

    async def shutdown(self) -> None:
        """
        Shutdown the client manager.

        Should be called during application shutdown.
        """
        async with self._lock:
            if not self._initialized:
                logger.warning("HikClientManager not initialized, nothing to shutdown")
                return

            # Save current token before closing
            if self._client and self._client.token_data and self._token_manager:
                try:
                    await self._token_manager.save_token_data(self._client.token_data)
                    logger.info("Token saved before shutdown")
                except Exception as e:
                    logger.error("Failed to save token during shutdown: %s" % str(e))

            # Close the client
            if self._client:
                await self._client.close()
                self._client = None

            self._token_manager = None
            self._redis = None
            self._initialized = False

            logger.info("HikClientManager shutdown complete")

    async def get_client(self) -> HikClient:
        """
        Get the shared HikClient instance.

        Returns:
            HikClient instance

        Raises:
            RuntimeError: If manager not initialized
        """
        if not self.is_initialized or not self._client:
            raise RuntimeError(
                "HikClientManager not initialized. "
                "Call initialize() during application startup."
            )

        # Sync token with cache before returning client
        try:
            await self._sync_token_with_cache()
        except Exception as e:
            logger.error("Failed to sync token from cache: %s" % str(e))
            # If token sync fails due to corruption, clear and re-authenticate
            if self._token_manager:
                logger.warning("Clearing corrupted token and re-authenticating")
                await self._token_manager.clear_token()
                await self._client._authenticate(expired=True)
                await self._token_manager.save_token_data(self._client.token_data)

        return self._client

    async def refresh_token(self) -> dict[str, Any]:
        """
        Manually trigger token refresh.

        Useful for testing or recovering from token issues.

        Returns:
            Dictionary containing new token data
        """
        if not self.is_initialized or not self._client:
            raise RuntimeError("HikClientManager not initialized")

        # Acquire distributed lock to ensure only one process refreshes
        if self._token_manager:
            lock_acquired = await self._token_manager.acquire_distributed_lock(
                timeout=10.0
            )
            if not lock_acquired:
                logger.warning("Another process is refreshing token, waiting...")
                # Wait a bit and get the new token from cache
                await asyncio.sleep(2)
                token_data = await self._token_manager.get_token_data()
                if token_data:
                    return token_data
                raise RuntimeError("Failed to acquire lock and no token available")
        else:
            lock_acquired = False

        try:
            async with self._lock:
                logger.info("Manually refreshing token...")
                await self._client._authenticate(expired=True)

                # Save refreshed token
                if self._client.token_data and self._token_manager:
                    await self._token_manager.save_token_data(self._client.token_data)

                return self._client.token_data
        finally:
            if lock_acquired and self._token_manager:
                await self._token_manager.release_distributed_lock()

    async def _sync_token_with_cache(self) -> None:
        """
        Sync client's token with cached token.

        Ensures client uses the latest token from cache (in case another
        process refreshed it).
        """
        if not self._token_manager or not self._client:
            return

        # Check if cached token is different and valid
        cached_token = await self._token_manager.get_valid_token()

        if cached_token and cached_token != self._client._token:
            logger.info("Updating client with newer cached token")
            cached_data = await self._token_manager.get_token_data()

            if cached_data:
                self._client._token = cached_data.get("access_token")
                self._client._token_expire_time = cached_data.get("expire_time")
                self._client._user_id = cached_data.get("user_id")
                self._client.token_data = cached_data

    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized


# Global singleton instance
_client_manager = HikClientManager()


async def get_hik_client_manager() -> HikClientManager:
    """
    Get the global HikClientManager instance.

    Returns:
        HikClientManager singleton instance
    """
    return _client_manager


async def get_hik_client() -> HikClient:
    """
    FastAPI dependency to get HikClient instance.

    Usage:
        @app.get("/some-endpoint")
        async def endpoint(client: HikClient = Depends(get_hik_client)):
            result = await client.get_devices()
            return result

    Returns:
        HikClient instance
    """
    manager = await get_hik_client_manager()
    return await manager.get_client()
