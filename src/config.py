"""Configuration for proxy pool collector."""

import os
from typing import Final

# Validation settings
HTTP_TEST_URL: Final[str] = os.getenv("HTTP_TEST_URL", "http://httpbin.org/ip")
HTTPS_TEST_URL: Final[str] = os.getenv("HTTPS_TEST_URL", "https://www.qq.com")
VALIDATION_TIMEOUT: Final[int] = int(os.getenv("VALIDATION_TIMEOUT", "5"))

# Concurrency settings
MAX_FETCH_WORKERS: Final[int] = int(os.getenv("MAX_FETCH_WORKERS", "10"))
MAX_VALIDATION_WORKERS: Final[int] = int(os.getenv("MAX_VALIDATION_WORKERS", "300"))

# User agents for requests
USER_AGENTS: Final[list[str]] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Request settings
REQUEST_TIMEOUT: Final[int] = int(os.getenv("REQUEST_TIMEOUT", "15"))
REQUEST_RETRY: Final[int] = int(os.getenv("REQUEST_RETRY", "2"))

# Logging
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
