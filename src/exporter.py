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
    Export HTTP proxies with http:// prefix.

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to

    Returns:
        Number of proxies exported
    """
    output_file = output_dir / "http_proxies.txt"
    with open(output_file, "w") as f:
        for proxy in proxies:
            f.write(f"http://{proxy.proxy}\n")

    logger.info(f"Exported {len(proxies)} HTTP proxies to {output_file}")
    return len(proxies)


def export_https_proxies(proxies: list[ProxyInfo], output_dir: Path) -> int:
    """
    Export HTTPS-capable proxies with https:// prefix.

    Args:
        proxies: List of validated proxies
        output_dir: Directory to write files to

    Returns:
        Number of proxies exported
    """
    https_proxies = [p for p in proxies if p.https_works]
    output_file = output_dir / "https_proxies.txt"

    with open(output_file, "w") as f:
        for proxy in https_proxies:
            f.write(f"https://{proxy.proxy}\n")

    logger.info(f"Exported {len(https_proxies)} HTTPS proxies to {output_file}")
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
- **HTTP Proxies**: {http_count}
- **HTTPS Proxies**: {https_count}
- **Updated**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

## Files

| File | Description |
|------|-------------|
| `proxies.txt` | All proxies in plain text format (ip:port) |
| `proxies.json` | All proxies with metadata in JSON format |
| `http_proxies.txt` | HTTP proxies with http:// prefix |
| `https_proxies.txt` | HTTPS-capable proxies with https:// prefix |

## Quick Start

### Download Latest Proxies

```bash
# Download all proxies
curl -L https://github.com/{repo_name}/releases/latest/download/proxies.txt -o proxies.txt

# Download HTTPS proxies only
curl -L https://github.com/{repo_name}/releases/latest/download/https_proxies.txt -o https_proxies.txt
```

### Python Usage

```python
import requests

# Read proxies from file
with open('proxies.txt', 'r') as f:
    proxies = [line.strip() for line in f if line.strip()]

# Use a proxy
proxy = proxies[0]
response = requests.get(
    'http://httpbin.org/ip',
    proxies={{'http': f'http://{{proxy}}', 'https': f'http://{{proxy}}'}}
)
print(response.json())
```

### Shell Usage

```bash
# Get first proxy
PROXY=$(head -n 1 proxies.txt)

# Use with curl
curl -x http://$PROXY http://httpbin.org/ip

# Test proxy
curl -x http://$PROXY -I http://httpbin.org/ip
```

### JavaScript/Node.js Usage

```javascript
const {{ readFileSync }} = require('fs');
const axios = require('axios');

// Read proxies
const proxies = readFileSync('proxies.txt', 'utf8')
  .split('\\n')
  .filter(line => line.trim());

// Use a proxy
const proxy = proxies[0];
const [host, port] = proxy.split(':');

axios.get('http://httpbin.org/ip', {{
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

All proxies are validated against:
- **HTTP**: Tested with http://httpbin.org/ip (must return 200 OK)
- **HTTPS**: Tested with https://www.qq.com (must return 200 OK)
- **Timeout**: 10 seconds per test
- **Format**: Must match pattern `ip:port` or `username:password@ip:port`

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
        # Create empty files so workflow doesn't fail
        for filename in ["proxies.txt", "http_proxies.txt", "https_proxies.txt"]:
            (output_dir / filename).write_text("")
        (output_dir / "proxies.json").write_text(
            json.dumps({"count": 0, "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), "proxies": []})
        )
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
