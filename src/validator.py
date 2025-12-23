"""Proxy validator for HTTP/HTTPS connectivity."""

import re
import logging
import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx

from .config import HTTP_TEST_URL, HTTPS_TEST_URL, VALIDATION_TIMEOUT, USER_AGENTS

logger = logging.getLogger(__name__)

# Regex for proxy format: [username:password@]ip:port
PROXY_PATTERN = re.compile(r"^(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$")

VALIDATION_HEADERS = {
    "User-Agent": USER_AGENTS[0],
    "Accept": "*/*",
    "Connection": "keep-alive",
}


@dataclass
class ProxyInfo:
    """Information about a validated proxy."""

    proxy: str
    http_works: bool
    https_works: bool
    source: str = "unknown"

    @property
    def is_valid(self) -> bool:
        """Check if proxy is valid (at least HTTP works)."""
        return self.http_works


def is_valid_format(proxy: str) -> bool:
    """
    Check if proxy string matches expected format.

    Args:
        proxy: Proxy string (e.g., "1.2.3.4:8080" or "user:pass@1.2.3.4:8080")

    Returns:
        True if format is valid
    """
    return bool(PROXY_PATTERN.match(proxy))


async def test_http(client: httpx.AsyncClient, proxy: str) -> bool:
    """
    Test if proxy works for HTTP requests.

    Args:
        client: httpx AsyncClient instance
        proxy: Proxy string in format "ip:port"

    Returns:
        True if proxy works for HTTP
    """
    proxy_url = f"http://{proxy}"

    try:
        response = await client.head(
            HTTP_TEST_URL,
            headers=VALIDATION_HEADERS,
            proxy=proxy_url,
            timeout=VALIDATION_TIMEOUT,
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"HTTP test failed for {proxy}: {e}")
        return False


async def test_https(client: httpx.AsyncClient, proxy: str) -> bool:
    """
    Test if proxy works for HTTPS requests.

    Args:
        client: httpx AsyncClient instance
        proxy: Proxy string in format "ip:port"

    Returns:
        True if proxy works for HTTPS
    """
    # Use https scheme for HTTPS testing
    proxy_url = f"http://{proxy}"

    try:
        response = await client.head(
            HTTPS_TEST_URL,
            headers=VALIDATION_HEADERS,
            proxy=proxy_url,
            timeout=VALIDATION_TIMEOUT,
            verify=False,  # Ignore SSL verification for proxy testing
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"HTTPS test failed for {proxy}: {e}")
        return False


async def validate_proxy(proxy: str, source: str = "unknown") -> Optional[ProxyInfo]:
    """
    Validate a proxy for both HTTP and HTTPS.

    Args:
        proxy: Proxy string in format "ip:port"
        source: Source name where proxy was fetched from

    Returns:
        ProxyInfo if proxy is valid (HTTP works), None otherwise
    """
    # Format validation
    if not is_valid_format(proxy):
        logger.debug(f"Invalid format: {proxy}")
        return None

    # Test HTTP and HTTPS in parallel
    async with httpx.AsyncClient(verify=False) as client:
        # Run both tests concurrently
        http_result, https_result = await asyncio.gather(
            test_http(client, proxy),
            test_https(client, proxy),
            return_exceptions=True
        )

        # Handle exceptions from gather
        http_works = http_result if isinstance(http_result, bool) else False
        https_works = https_result if isinstance(https_result, bool) else False

        # Only return if HTTP works
        if not http_works:
            return None

        return ProxyInfo(
            proxy=proxy,
            http_works=True,
            https_works=https_works,
            source=source,
        )
