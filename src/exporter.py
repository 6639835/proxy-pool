"""Export validated proxies to various file formats."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .validator import ProxyInfo

logger = logging.getLogger(__name__)


def export_to_txt(proxies: list[ProxyInfo], output_dir: Path) -> int:
    """
    Export all proxies to plain text file (one per line).

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to

    Returns:
        Number of proxies exported
    """
    output_file = output_dir / "proxies.txt"
    with open(output_file, "w") as f:
        if not proxies:
            f.write("# No proxies available\n")
        else:
            for proxy in proxies:
                f.write(f"{proxy.proxy}\n")

    logger.info(f"Exported {len(proxies)} proxies to {output_file}")
    return len(proxies)


def export_to_json(proxies: list[ProxyInfo], output_dir: Path) -> int:
    """
    Export proxies to JSON with metadata.

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to

    Returns:
        Number of proxies exported
    """
    output_file = output_dir / "proxies.json"

    proxy_list = [
        {
            "proxy": p.proxy,
            "http": p.http_works,
            "https": p.https_works,
            "source": p.source,
        }
        for p in proxies
    ]

    data = {
        "count": len(proxy_list),
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "proxies": proxy_list,
    }

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Exported {len(proxies)} proxies to {output_file}")
    return len(proxies)


def export_http_proxies(proxies: list[ProxyInfo], output_dir: Path) -> int:
    """
    Export all proxies with http:// prefix (ready to use).

    Note: ALL proxies should be used with http:// prefix, regardless of
    whether they support HTTPS traffic. The http:// refers to the proxy
    connection protocol, not the target URL protocol.

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to

    Returns:
        Number of proxies exported
    """
    output_file = output_dir / "http_proxies.txt"
    with open(output_file, "w") as f:
        if not proxies:
            f.write("# No proxies available\n")
        else:
            f.write("# All proxies - use with http:// prefix as shown\n")
            f.write("# These proxies work for HTTP requests\n")
            f.write("# Some may also support HTTPS (see https_capable_proxies.txt)\n")
            f.write("#\n")
            for proxy in proxies:
                f.write(f"http://{proxy.proxy}\n")

    logger.info(f"Exported {len(proxies)} proxies to {output_file}")
    return len(proxies)


def export_https_proxies(proxies: list[ProxyInfo], output_dir: Path) -> int:
    """
    Export HTTPS-capable proxies with http:// prefix (ready to use).

    These proxies can tunnel HTTPS traffic, but they should still be
    configured with http:// prefix. The HTTPS refers to the target URL
    protocol, not the proxy connection protocol.

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to

    Returns:
        Number of HTTPS-capable proxies exported
    """
    https_proxies = [p for p in proxies if p.https_works]
    output_file = output_dir / "https_capable_proxies.txt"

    with open(output_file, "w") as f:
        if not https_proxies:
            f.write("# No HTTPS-capable proxies available\n")
        else:
            f.write("# HTTPS-capable proxies - use with http:// prefix as shown\n")
            f.write("# These proxies can handle both HTTP and HTTPS requests\n")
            f.write("# Use like: httpx.AsyncClient(proxy='http://ip:port')\n")
            f.write("#\n")
            for proxy in https_proxies:
                f.write(f"http://{proxy.proxy}\n")

    logger.info(f"Exported {len(https_proxies)} HTTPS-capable proxies to {output_file}")
    return len(https_proxies)


def generate_readme(
    total_count: int,
    http_count: int,
    https_count: int,
    output_dir: Path,
    repo_name: Optional[str] = None,
) -> None:
    """
    Generate README with usage instructions.

    Args:
        total_count: Total number of proxies
        http_count: Number of HTTP proxies
        https_count: Number of HTTPS proxies
        output_dir: Directory to write files to
        repo_name: Optional GitHub repository name
    """
    output_file = output_dir / "README.md"

    if repo_name is None:
        repo_name = "YOUR_USERNAME/proxy-pool"

    readme_content = f"""# Proxy Pool Export

## Summary

- **Total Proxies**: {total_count}
- **All Work for HTTP**: {http_count}
- **HTTPS-Capable**: {https_count}
- **Updated**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

## Files

| File | Description |
|------|-------------|
| `proxies.txt` | All proxies in plain text format (ip:port) |
| `proxies.json` | All proxies with metadata in JSON format |
| `http_proxies.txt` | All proxies with http:// prefix (ready to use) |
| `https_capable_proxies.txt` | HTTPS-capable proxies with http:// prefix (ready to use) |

## Understanding HTTP vs HTTPS Proxies

**Important**: ALL proxies should be used with `http://` prefix, regardless of capability.

- **http_proxies.txt**: Contains all validated proxies. These work for HTTP requests.
- **https_capable_proxies.txt**: Contains proxies that can also tunnel HTTPS traffic.

The `http://` prefix refers to how you connect to the proxy, not what traffic it can handle.

## Quick Start

### Download Latest Proxies

```bash
# Download all proxies (plain format)
curl -L https://github.com/{repo_name}/releases/latest/download/proxies.txt -o proxies.txt

# Download HTTPS-capable proxies (ready to use with http:// prefix)
curl -L https://github.com/{repo_name}/releases/latest/download/https_capable_proxies.txt -o https_proxies.txt
```

### Python Usage

```python
import httpx
import asyncio

# Read proxies from file (already has http:// prefix)
with open('http_proxies.txt', 'r') as f:
    proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]

async def test_proxy():
    # Use proxy directly - format is already correct
    proxy = proxies[0]  # e.g., "http://1.2.3.4:8080"

    async with httpx.AsyncClient(proxy=proxy, verify=False, timeout=5) as client:
        # Test with HTTP request
        response = await client.get('http://httpbin.org/ip')
        print(f'HTTP request via proxy: {{response.json()}}')

        # Same proxy can handle HTTPS if it's HTTPS-capable
        response = await client.get('https://httpbin.org/ip')
        print(f'HTTPS request via proxy: {{response.json()}}')

asyncio.run(test_proxy())
```

### Requests Library Usage

```python
import requests

# Read proxy (already formatted correctly)
with open('http_proxies.txt', 'r') as f:
    proxy = [line.strip() for line in f if line.strip() and not line.startswith('#')][0]

# Use for both HTTP and HTTPS requests
proxies = {{'http': proxy, 'https': proxy}}

response = requests.get('http://httpbin.org/ip', proxies=proxies)
print(response.json())
```

### Shell Usage

```bash
# Read proxy from file (already formatted)
PROXY=$(grep -v '^#' http_proxies.txt | head -n 1)

# Use with curl (proxy format is ready to use)
curl -x "$PROXY" http://httpbin.org/ip

# Test HTTPS through the same proxy
curl -x "$PROXY" https://httpbin.org/ip
```

### JavaScript/Node.js Usage

```javascript
const {{ readFileSync }} = require('fs');
const axios = require('axios');

// Read proxies (skip comment lines)
const proxies = readFileSync('http_proxies.txt', 'utf8')
  .split('\\n')
  .filter(line => line.trim() && !line.startsWith('#'));

// Parse proxy URL
const proxyUrl = proxies[0];  // e.g., "http://1.2.3.4:8080"
const match = proxyUrl.match(/http:\\/\\/(.*?):(\\d+)/);
const [, host, port] = match;

// Use for both HTTP and HTTPS
axios.get('https://httpbin.org/ip', {{
  proxy: {{ host, port: parseInt(port) }}
}}).then(response => console.log(response.data));
```

## Important Notes

⚠️ **Free Proxy Limitations**:
- Free proxies have limited reliability and may fail frequently
- Proxies are validated at collection time but may become unavailable quickly
- Success rates are typically low (5-20% of proxies work at any given time)
- Not recommended for production use

✅ **Best Practices**:
- Always implement retry logic with multiple proxies
- Validate proxies before use in your application
- Consider paid proxy services for production workloads
- Respect rate limits and terms of service of target websites

## Validation Details

All proxies are validated using async concurrent testing:

### Testing Process
- **HTTP Test**: Connects via `http://proxy` to `http://www.google.com`
  - Must return 200 OK to be included
- **HTTPS Test**: Connects via `http://proxy` to `https://www.google.com`
  - Tests HTTPS tunneling capability (CONNECT method)
  - Proxies passing this test go in `https_capable_proxies.txt`
- **Timeout**: 5 seconds per test
- **Format**: Must match pattern `ip:port` or `username:password@ip:port`
- **Concurrency**: Up to 300 simultaneous validation workers

### Important Clarification
**All proxies use `http://` connection protocol**, even when tunneling HTTPS:
- Proxy connection: Always `http://proxy_ip:port`
- Target URL: Can be `http://` or `https://` depending on the site
- HTTPS-capable proxies use HTTP CONNECT tunneling for HTTPS targets

## Sources

Proxies are collected from 16+ free proxy sources including:
- ProxyScrape API
- GitHub proxy lists (TheSpeedX, clarketm)
- free-proxy-list.net
- GeoNode API
- Various Chinese proxy sites

## Update Frequency

This list is automatically updated daily via GitHub Actions.

## License

Free proxies are provided as-is. Use at your own risk.
"""

    with open(output_file, "w") as f:
        f.write(readme_content)

    logger.info(f"Generated README at {output_file}")


def export_all(
    proxies: list[ProxyInfo],
    output_dir: Path = Path("."),
    repo_name: Optional[str] = None,
) -> dict[str, int]:
    """
    Export proxies to all formats.

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to (default: current directory)
        repo_name: Optional GitHub repository name for README

    Returns:
        Dictionary with export statistics
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not proxies:
        logger.warning("No proxies to export!")
        # Export functions will create files with placeholder comments
        export_to_txt([], output_dir)
        export_to_json([], output_dir)
        export_http_proxies([], output_dir)
        export_https_proxies([], output_dir)
        generate_readme(0, 0, 0, output_dir, repo_name)
        return {"total": 0, "http": 0, "https": 0}

    logger.info(f"Exporting {len(proxies)} proxies to {output_dir}...")

    # Export to different formats
    total_count = export_to_txt(proxies, output_dir)
    export_to_json(proxies, output_dir)
    http_count = export_http_proxies(proxies, output_dir)
    https_count = export_https_proxies(proxies, output_dir)

    # Generate README
    generate_readme(total_count, http_count, https_count, output_dir, repo_name)

    stats = {
        "total": total_count,
        "http": http_count,
        "https": https_count,
    }

    logger.info(f"Export complete: {stats}")
    return stats
