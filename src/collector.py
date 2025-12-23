"""Main collector that orchestrates proxy fetching and validation."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

from .config import MAX_FETCH_WORKERS, MAX_VALIDATION_WORKERS
from .fetchers import FETCHERS
from .validator import ProxyInfo, validate_proxy

logger = logging.getLogger(__name__)


def fetch_from_source(source_name: str, fetcher_func: callable) -> list[tuple[str, str]]:
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


def validate_proxies(proxy_map: dict[str, str]) -> Iterator[ProxyInfo]:
    """
    Validate all proxies concurrently.

    Args:
        proxy_map: Dictionary mapping proxy to source name

    Yields:
        ProxyInfo for each valid proxy
    """
    total = len(proxy_map)
    validated_count = 0
    failed_count = 0

    logger.info(f"Starting validation of {total} unique proxies...")

    with ThreadPoolExecutor(max_workers=MAX_VALIDATION_WORKERS) as executor:
        futures = {
            executor.submit(validate_proxy, proxy, source): proxy
            for proxy, source in proxy_map.items()
        }

        for i, future in enumerate(as_completed(futures), 1):
            proxy = futures[future]
            try:
                result = future.result()
                if result and result.is_valid:
                    validated_count += 1
                    yield result
                    logger.info(
                        f"[{i}/{total}] ✓ {proxy} (HTTPS: {result.https_works}) from {result.source}"
                    )
                else:
                    failed_count += 1
                    logger.debug(f"[{i}/{total}] ✗ {proxy} failed validation")
            except Exception as e:
                failed_count += 1
                logger.error(f"[{i}/{total}] ✗ {proxy} validation error: {e}")

            # Progress update every 10 proxies
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total} validated ({validated_count} valid, {failed_count} failed)")

    logger.info(f"Validation complete: {validated_count} valid, {failed_count} failed")


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

    # Step 3: Validate
    valid_proxies = list(validate_proxies(unique_proxies))

    logger.info(f"Collection complete: {len(valid_proxies)} valid proxies")
    return valid_proxies
