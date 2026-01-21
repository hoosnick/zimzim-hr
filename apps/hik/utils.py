import base64
import io
import time
from datetime import datetime
from typing import Any

import orjson
from PIL import Image


def is_token_expired(expire_time: int, margin_seconds: int = 300) -> bool:
    """
    Check if token is expired or about to expire

    Args:
        expire_time: Token expiration timestamp
        margin_seconds: Safety margin in seconds (default: 5 minutes)

    Returns:
        True if token is expired or about to expire within margin
    """
    current_time = int(time.time())
    # Add safety margin to prevent mid-request token expiry
    return current_time >= (expire_time - margin_seconds)


def serialize_json(data: Any) -> bytes:
    """
    Serialize data to JSON using orjson for maximum performance

    Args:
        data: Data to serialize

    Returns:
        JSON bytes
    """
    return orjson.dumps(
        data,
        option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY,
    )


def deserialize_json(data: bytes | str) -> dict[str, Any]:
    """
    Deserialize JSON data using orjson for maximum performance

    Args:
        data: JSON bytes or string

    Returns:
        Deserialized Python object
    """
    return orjson.loads(data)


def format_iso_datetime(dt: datetime) -> str:
    """
    Format datetime to ISO 8601 format required by HikCentral API

    Args:
        dt: Datetime object

    Returns:
        ISO 8601 formatted string (e.g., "2024-01-01T00:00:00+08:00")
    """
    if dt.tzinfo is None:
        # Assume UTC+8 if no timezone info
        return dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    return dt.isoformat()


def parse_iso_datetime(dt_str: str) -> datetime:
    """
    Parse ISO 8601 datetime string

    Args:
        dt_str: ISO 8601 formatted string

    Returns:
        Datetime object
    """
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def resize_image_optimal(
    image_data: bytes,
    max_width: int = 600,
    max_height: int = 800,
    maintain_aspect: bool = True,
    quality: int = 85,
    max_file_size: int = 200 * 1024,
) -> bytes:
    """
    Resize image to optimal dimensions for Hikvision face recognition

    Hikvision requirements:
    - Format: JPG
    - Aspect ratio: 3:4
    - Size: 600×800 (recommended) or 480×640
    - File size: ≤ 200 KB
    - Face should occupy 60-70% of frame

    Args:
        image_data: Original image data in bytes
        max_width: Target width in pixels (default: 600 for 3:4 ratio)
        max_height: Target height in pixels (default: 800 for 3:4 ratio)
        maintain_aspect: Whether to maintain aspect ratio (default: True)
        quality: JPEG quality 1-100 (default: 85)
        max_file_size: Maximum file size in bytes (default: 200 KB)

    Returns:
        Resized image data in bytes (JPEG format)
    """
    # Load image from bytes
    img = Image.open(io.BytesIO(image_data))

    # Convert to RGB if necessary (remove alpha channel)
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Calculate new dimensions maintaining 3:4 aspect ratio
    target_ratio = max_width / max_height  # 3:4 = 0.75
    img_ratio = img.width / img.height

    if maintain_aspect:
        # Crop to target aspect ratio first, then resize
        if img_ratio > target_ratio:
            # Image is wider - crop width
            new_img_width = int(img.height * target_ratio)
            left = (img.width - new_img_width) // 2
            img = img.crop((left, 0, left + new_img_width, img.height))
        elif img_ratio < target_ratio:
            # Image is taller - crop height
            new_img_height = int(img.width / target_ratio)
            top = (img.height - new_img_height) // 2
            img = img.crop((0, top, img.width, top + new_img_height))

        new_width = max_width
        new_height = max_height
    else:
        new_width = min(img.width, max_width)
        new_height = min(img.height, max_height)

    # Resize image with high-quality resampling
    if new_width != img.width or new_height != img.height:
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save to bytes with quality adjustment to meet file size requirement
    output = io.BytesIO()
    current_quality = quality

    # Try to compress to meet file size limit
    for _ in range(5):  # Max 5 attempts
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=current_quality, optimize=True)
        output.seek(0)

        if output.getbuffer().nbytes <= max_file_size or current_quality <= 50:
            break

        # Reduce quality by 10 for next iteration
        current_quality -= 10

    output.seek(0)
    return output.read()


def image_to_base64(image_data: bytes, resize: bool = True, **resize_kwargs) -> str:
    """
    Convert image to base64 string, optionally resizing it first

    Default settings are optimized for Hikvision face recognition:
    - 600×800 pixels (3:4 aspect ratio)
    - ≤ 200 KB file size

    Args:
        image_data: Image data in bytes
        resize: Whether to resize image (default: True)
        **resize_kwargs: Additional arguments for resize_image_optimal()

    Returns:
        Base64 encoded string
    """
    if resize:
        # Default resize parameters optimized for Hikvision face recognition
        default_kwargs = {
            "max_width": 600,
            "max_height": 800,
            "maintain_aspect": True,
            "quality": 85,
            "max_file_size": 200 * 1024,
        }
        default_kwargs.update(resize_kwargs)
        image_data = resize_image_optimal(image_data, **default_kwargs)

    return base64.b64encode(image_data).decode("utf-8")


def base64_to_image(base64_str: str) -> bytes:
    """
    Convert base64 string to image bytes

    Args:
        base64_str: Base64 encoded string

    Returns:
        Image data in bytes
    """
    return base64.b64decode(base64_str)
