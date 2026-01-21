"""
Token Manager for HikVision API tokens with Redis caching.

Provides centralized token management with persistence across app restarts
and sharing between different processes (poller, API server, workers).
"""

import asyncio
import time
from typing import Any, Optional

from loguru import logger
from redis.asyncio import Redis

from apps.hik.utils import is_token_expired


class TokenManager:
    """
    Manages HikVision API tokens with Redis caching and automatic refresh.

    Features:
    - Token persistence across app restarts
    - Shared tokens between multiple processes
    - Automatic token refresh before expiration
    - Thread-safe token acquisition with distributed locks
    """

    def __init__(
        self,
        redis_client: Redis,
        app_key: str,
        secret_key: str,
        cache_key_prefix: str = "hikvision:token",
    ):
        """
        Initialize Token Manager.

        Args:
            redis_client: Redis async client instance
            app_key: HikVision API app key
            secret_key: HikVision API secret key
            cache_key_prefix: Redis key prefix for token storage
        """
        self.redis = redis_client
        self.app_key = app_key
        self.secret_key = secret_key
        self.cache_key_prefix = cache_key_prefix

        # Local cache to reduce Redis roundtrips
        self._local_cache: Optional[dict[str, Any]] = None
        self._local_cache_time: Optional[float] = None
        self._local_cache_ttl = 60.0  # Re-check Redis every 60 seconds

        self._lock = asyncio.Lock()

    @property
    def _token_key(self) -> str:
        """Redis key for storing token data."""
        return f"{self.cache_key_prefix}:{self.app_key}"

    @property
    def _lock_key(self) -> str:
        """Redis key for distributed lock."""
        return f"{self.cache_key_prefix}:lock:{self.app_key}"

    async def get_token_data(self) -> Optional[dict[str, Any]]:
        """
        Get current token data from Redis or local cache.

        Returns:
            Token data dictionary with access_token, expire_time, user_id
            or None if no token exists
        """
        # Check local cache first
        if self._is_local_cache_valid():
            logger.debug("Using local cached token data")
            return self._local_cache

        # Fetch from Redis
        async with self._lock:
            token_data = await self._fetch_from_redis()

            if token_data:
                # Update local cache
                self._local_cache = token_data
                self._local_cache_time = time.time()

            return token_data

    async def get_valid_token(self) -> Optional[str]:
        """
        Get a valid token, refreshing if necessary.

        Returns:
            Valid access token string or None if unavailable
        """
        token_data = await self.get_token_data()

        if not token_data:
            logger.warning("No token data available in cache")
            return None

        expire_time = token_data.get("expire_time")
        if not expire_time:
            logger.warning("Token data missing expire_time")
            return None

        # Check if token needs refresh (with safety margin)
        if is_token_expired(expire_time):
            logger.info("Token expired or about to expire, needs refresh")
            return None

        return token_data.get("access_token")

    async def save_token_data(self, token_data: dict[str, Any]) -> None:
        """
        Save token data to Redis and update local cache.
        Uses distributed lock to prevent concurrent writes from multiple processes.

        Args:
            token_data: Dictionary containing access_token, expire_time, user_id
        """
        if not token_data.get("access_token"):
            raise ValueError("Token data must contain access_token")

        if not token_data.get("expire_time"):
            raise ValueError("Token data must contain expire_time")

        # Acquire distributed lock to prevent race conditions
        lock_acquired = await self.acquire_distributed_lock(timeout=5.0)

        try:
            async with self._lock:
                # Calculate TTL for Redis (token lifetime)
                expire_time = token_data["expire_time"]
                current_time = int(time.time())
                ttl = expire_time - current_time

                if ttl <= 0:
                    logger.warning("Attempting to save already expired token")
                    return

                # Save to Redis with TTL
                await self.redis.hset(
                    self._token_key,
                    mapping={
                        "access_token": token_data["access_token"],
                        "expire_time": str(token_data["expire_time"]),
                        "user_id": token_data.get("user_id", ""),
                    },
                )
                await self.redis.expire(self._token_key, ttl)

                # Update local cache
                self._local_cache = token_data
                self._local_cache_time = time.time()

                logger.info(
                    f"Token saved to cache. User: {token_data.get('user_id')}, "
                    f"Expires in: {ttl} seconds ({ttl / 3600:.1f} hours)"
                )
        finally:
            # Always release the distributed lock
            if lock_acquired:
                await self.release_distributed_lock()

    async def clear_token(self) -> None:
        """Clear token from both Redis and local cache."""
        async with self._lock:
            await self.redis.delete(self._token_key)
            self._local_cache = None
            self._local_cache_time = None
            logger.info("Token cleared from cache")

    async def _fetch_from_redis(self) -> Optional[dict[str, Any]]:
        """Fetch token data from Redis."""
        token_hash = await self.redis.hgetall(self._token_key)

        if not token_hash:
            return None

        # Redis returns bytes, convert to strings
        token_data = {
            key.decode() if isinstance(key, bytes) else key: (
                value.decode() if isinstance(value, bytes) else value
            )
            for key, value in token_hash.items()
        }

        # Convert expire_time back to int
        if "expire_time" in token_data:
            token_data["expire_time"] = int(token_data["expire_time"])

        return token_data

    def _is_local_cache_valid(self) -> bool:
        """Check if local cache is still valid."""
        if not self._local_cache or self._local_cache_time is None:
            return False

        # Check if cache is too old
        cache_age = time.time() - self._local_cache_time
        if cache_age > self._local_cache_ttl:
            return False

        # Check if token itself is expired
        expire_time = self._local_cache.get("expire_time")
        if not expire_time or is_token_expired(expire_time):
            return False

        return True

    async def acquire_distributed_lock(
        self,
        timeout: float = 10.0,
        lock_ttl: int = 30,
    ) -> bool:
        """
        Acquire a distributed lock for token refresh operations.

        Args:
            timeout: How long to wait for lock acquisition
            lock_ttl: Lock time-to-live in seconds

        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Try to acquire lock with NX (only set if not exists)
            acquired = await self.redis.set(
                self._lock_key,
                "1",
                nx=True,
                ex=lock_ttl,
            )

            if acquired:
                logger.debug("Distributed lock acquired")
                return True

            # Lock held by another process, wait a bit
            await asyncio.sleep(0.1)

        logger.warning("Failed to acquire distributed lock after %s seconds" % timeout)
        return False

    async def release_distributed_lock(self) -> None:
        """Release the distributed lock."""
        await self.redis.delete(self._lock_key)
        logger.debug("Distributed lock released")
