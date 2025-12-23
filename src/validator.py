"""Proxy validator for HTTP/HTTPS connectivity."""

import re
import logging
from dataclasses import dataclass
from typing import Optional

import requests

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


def test_http(proxy: str) -> bool:
    """
    Test if proxy works for HTTP requests.

    Args:
        proxy: Proxy string in format "ip:port"

    Returns:
        True if proxy works for HTTP
    """
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}",
    }

    try:
        response = requests.head(
            HTTP_TEST_URL,
            headers=VALIDATION_HEADERS,
            proxies=proxies,
            timeout=VALIDATION_TIMEOUT,
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"HTTP test failed for {proxy}: {e}")
        return False


def test_https(proxy: str) -> bool:
    """
    Test if proxy works for HTTPS requests.

    Args:
        proxy: Proxy string in format "ip:port"

    Returns:
        True if proxy works for HTTPS
    """
    proxies = {
        "http": f"http://{proxy}",
        "https": f"https://{proxy}",
    }

    try:
        response = requests.head(
            HTTPS_TEST_URL,
            headers=VALIDATION_HEADERS,
            proxies=proxies,
            timeout=VALIDATION_TIMEOUT,
            verify=False,  # Ignore SSL verification for proxy testing
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"HTTPS test failed for {proxy}: {e}")
        return False


def validate_proxy(proxy: str, source: str = "unknown") -> Optional[ProxyInfo]:
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

    # HTTP validation (required)
    http_works = test_http(proxy)
    if not http_works:
        return None

    # HTTPS validation (optional, only if HTTP works)
    https_works = test_https(proxy)

    return ProxyInfo(
        proxy=proxy,
        http_works=True,
        https_works=https_works,
        source=source,
    )
