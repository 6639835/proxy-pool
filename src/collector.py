"""Main collector that orchestrates proxy fetching and validation."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from .config import MAX_FETCH_WORKERS, MAX_VALIDATION_WORKERS
from .fetchers import FETCHERS
from .validator import ProxyInfo, validate_proxy

logger = logging.getLogger(__name__)


def fetch_from_source(
    source_name: str, fetcher_func: callable
) -> list[tuple[str, str]]:
    """
    Fetch proxies from a single source.

    Args:
        source_name: Name of the source
        fetcher_func: Function that yields proxies

    Returns:
        List of (proxy, source_name) tuples
    """
    proxies = []
    try:
        logger.info(f"Fetching from {source_name}...")
        for proxy in fetcher_func():
            proxies.append((proxy, source_name))
        logger.info(f"Fetched {len(proxies)} proxies from {source_name}")
    except Exception as e:
        logger.error(f"Error fetching from {source_name}: {e}")

    return proxies


def fetch_all_proxies() -> list[tuple[str, str]]:
    """
    Fetch proxies from all sources concurrently.

    Returns:
        List of (proxy, source_name) tuples (may contain duplicates)
    """
    all_proxies = []

    with ThreadPoolExecutor(max_workers=MAX_FETCH_WORKERS) as executor:
        futures = {
            executor.submit(fetch_from_source, name, func): name
            for name, func in FETCHERS.items()
        }

        for future in as_completed(futures):
            source_name = futures[future]
            try:
                proxies = future.result()
                all_proxies.extend(proxies)
            except Exception as e:
                logger.error(f"Failed to collect from {source_name}: {e}")

    logger.info(f"Total proxies fetched: {len(all_proxies)}")
    return all_proxies


def deduplicate_proxies(proxies: list[tuple[str, str]]) -> dict[str, str]:
    """
    Remove duplicate proxies, keeping track of sources.

    Args:
        proxies: List of (proxy, source_name) tuples

    Returns:
        Dictionary mapping proxy to source name (last source if duplicates)
    """
    proxy_map = {}
    for proxy, source in proxies:
        proxy = proxy.strip()
        if proxy:
            proxy_map[proxy] = source

    logger.info(f"Unique proxies after deduplication: {len(proxy_map)}")
    return proxy_map


async def validate_single_proxy(
    semaphore: asyncio.Semaphore,
    proxy: str,
    source: str,
    index: int,
    total: int
) -> tuple[int, Optional[ProxyInfo]]:
    """
    Validate a single proxy with semaphore for concurrency control.

    Args:
        semaphore: Asyncio semaphore for concurrency limiting
        proxy: Proxy string
        source: Source name
        index: Current index (for logging)
        total: Total number of proxies

    Returns:
        Tuple of (index, ProxyInfo or None)
    """
    async with semaphore:
        try:
            result = await validate_proxy(proxy, source)
            if result and result.is_valid:
                logger.info(
                    f"[{index}/{total}] ✓ {proxy} (HTTPS: {result.https_works}) from {result.source}"
                )
            else:
                logger.debug(f"[{index}/{total}] ✗ {proxy} failed validation")
            return (index, result)
        except Exception as e:
            logger.error(f"[{index}/{total}] ✗ {proxy} validation error: {e}")
            return (index, None)


async def validate_proxies_async(proxy_map: dict[str, str]) -> list[ProxyInfo]:
    """
    Validate all proxies concurrently using asyncio.

    Args:
        proxy_map: Dictionary mapping proxy to source name

    Returns:
        List of valid ProxyInfo objects
    """
    total = len(proxy_map)
    logger.info(f"Starting async validation of {total} unique proxies...")

    # Semaphore to limit concurrency
    semaphore = asyncio.Semaphore(MAX_VALIDATION_WORKERS)

    # Create validation tasks
    tasks = [
        validate_single_proxy(semaphore, proxy, source, i, total)
        for i, (proxy, source) in enumerate(proxy_map.items(), 1)
    ]

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect valid proxies and count stats
    valid_proxies = []
    validated_count = 0
    failed_count = 0

    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            failed_count += 1
            logger.error(f"Task {i} raised exception: {result}")
        elif isinstance(result, tuple):
            _, proxy_info = result
            if proxy_info and proxy_info.is_valid:
                valid_proxies.append(proxy_info)
                validated_count += 1
            else:
                failed_count += 1

        # Progress update every 50 proxies (more frequent for async)
        if i % 50 == 0:
            logger.info(
                f"Progress: {i}/{total} validated ({validated_count} valid, {failed_count} failed)"
            )

    logger.info(f"Validation complete: {validated_count} valid, {failed_count} failed")
    return valid_proxies


def validate_proxies(proxy_map: dict[str, str]) -> list[ProxyInfo]:
    """
    Validate all proxies (sync wrapper for async validation).

    Args:
        proxy_map: Dictionary mapping proxy to source name

    Returns:
        List of valid ProxyInfo objects
    """
    return asyncio.run(validate_proxies_async(proxy_map))


def collect_proxies() -> list[ProxyInfo]:
    """
    Main collection function: fetch, deduplicate, and validate proxies.

    Returns:
        List of validated ProxyInfo objects
    """
    logger.info("Starting proxy collection...")

    # Step 1: Fetch from all sources
    raw_proxies = fetch_all_proxies()
    if not raw_proxies:
        logger.warning("No proxies fetched from any source!")
        return []

    # Step 2: Deduplicate
    unique_proxies = deduplicate_proxies(raw_proxies)
    if not unique_proxies:
        logger.warning("No unique proxies after deduplication!")
        return []

    # Step 3: Validate (now async)
    valid_proxies = validate_proxies(unique_proxies)

    logger.info(f"Collection complete: {len(valid_proxies)} valid proxies")
    return valid_proxies
