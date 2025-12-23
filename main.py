#!/usr/bin/env python3
"""
Proxy Pool Collector - GitHub Actions optimized version.

This script collects free proxies from multiple sources, validates them,
and exports to various file formats for use in your applications.

Usage:
    python main.py [--output-dir DIR] [--repo-name OWNER/REPO]

Environment Variables:
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR) - default: INFO
    MAX_FETCH_WORKERS: Number of concurrent fetcher threads - default: 10
    MAX_VALIDATION_WORKERS: Number of concurrent validation threads - default: 50
    VALIDATION_TIMEOUT: Proxy validation timeout in seconds - default: 10
"""

import argparse
import logging
import sys
import warnings
from pathlib import Path

# Suppress SSL warnings from requests
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Setup logging
from src.config import LOG_LEVEL

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for proxy collection."""
    parser = argparse.ArgumentParser(
        description="Collect and validate free proxies from multiple sources"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory for proxy files (default: current directory)",
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        help="GitHub repository name (e.g., 'username/repo') for README",
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("Proxy Pool Collector - Starting")
        logger.info("=" * 60)

        # Import here to ensure logging is configured first
        from src.collector import collect_proxies
        from src.exporter import export_all

        # Step 1: Collect and validate proxies
        proxies = collect_proxies()

        if not proxies:
            logger.warning("No valid proxies found!")
            logger.warning("This could mean:")
            logger.warning("  1. All proxies failed validation")
            logger.warning("  2. Network connectivity issues")
            logger.warning("  3. Proxy sources are down or changed")
            logger.warning("Creating empty export files...")

        # Step 2: Export to files
        stats = export_all(proxies, args.output_dir, args.repo_name)

        # Step 3: Summary
        logger.info("=" * 60)
        logger.info("Collection Summary:")
        logger.info(f"  Total proxies: {stats['total']}")
        logger.info(f"  HTTP proxies: {stats['http']}")
        logger.info(f"  HTTPS proxies: {stats['https']}")
        logger.info(f"  Output directory: {args.output_dir.absolute()}")
        logger.info("=" * 60)

        if stats['total'] == 0:
            logger.warning("No proxies were collected. Exit code: 1")
            return 1

        logger.info("Success! Proxy collection complete.")
        return 0

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
