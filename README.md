# Proxy Pool

> **Clean · Safe · Consistent · Observable · Maintainable**

A minimal, GitHub Actions-optimized proxy pool collector that gathers and validates free proxies from 16+ sources.

## Features

- **Minimal Dependencies**: Only `requests` and `lxml` required
- **Concurrent Processing**: Fast fetching and validation with ThreadPoolExecutor
- **Multiple Export Formats**: TXT, JSON, HTTP, HTTPS formats
- **Automated Updates**: Daily collection via GitHub Actions
- **Type-Safe**: Full type hints throughout codebase
- **Observable**: Comprehensive logging and progress tracking
- **Zero Infrastructure**: No database, no API server, just file exports

## Quick Start

### Download Latest Proxies

```bash
# Download all proxies (plain text)
curl -L https://github.com/YOUR_USERNAME/proxy-pool/releases/latest/download/proxies.txt -o proxies.txt

# Download HTTPS-capable proxies
curl -L https://github.com/YOUR_USERNAME/proxy-pool/releases/latest/download/https_proxies.txt -o https_proxies.txt

# Download JSON with metadata
curl -L https://github.com/YOUR_USERNAME/proxy-pool/releases/latest/download/proxies.json -o proxies.json
```

### Local Usage

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/proxy-pool.git
cd proxy-pool

# Install dependencies
pip install -r requirements.txt

# Run collection
python main.py

# Custom output directory
python main.py --output-dir ./output
```

## Usage Examples

### Python

```python
import requests

# Load proxies from file
with open('proxies.txt', 'r') as f:
    proxies = [line.strip() for line in f if line.strip()]

# Use a proxy
proxy = proxies[0]
response = requests.get(
    'http://httpbin.org/ip',
    proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
    timeout=10
)
print(response.json())
```

### Shell Script

```bash
#!/bin/bash

# Download latest proxies
curl -sL https://github.com/YOUR_USERNAME/proxy-pool/releases/latest/download/proxies.txt -o proxies.txt

# Test each proxy
while IFS= read -r proxy; do
  echo "Testing $proxy..."
  if curl -x "http://$proxy" -s -m 5 http://httpbin.org/ip > /dev/null; then
    echo "✓ $proxy works"
  else
    echo "✗ $proxy failed"
  fi
done < proxies.txt
```

### JavaScript/Node.js

```javascript
const fs = require('fs');
const axios = require('axios');

// Load proxies
const proxies = fs.readFileSync('proxies.txt', 'utf8')
  .split('\n')
  .filter(line => line.trim());

// Use a proxy
const [host, port] = proxies[0].split(':');
axios.get('http://httpbin.org/ip', {
  proxy: { host, port: parseInt(port) }
}).then(res => console.log(res.data));
```

## Architecture

### File Structure

```
proxy-pool/
├── .github/
│   └── workflows/
│       └── collect-proxies.yml    # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── config.py                  # Configuration constants
│   ├── fetchers.py                # 16 proxy source fetchers
│   ├── validator.py               # HTTP/HTTPS validation
│   ├── collector.py               # Orchestration logic
│   └── exporter.py                # File export functions
├── main.py                        # Entry point
├── requirements.txt               # Dependencies (2 packages)
└── README.md
```

### Data Flow

```
┌─────────────────┐
│  Fetch Proxies  │ → 16 sources, concurrent fetching
└────────┬────────┘
         ↓
┌─────────────────┐
│  Deduplicate    │ → Remove duplicates, track sources
└────────┬────────┘
         ↓
┌─────────────────┐
│  Validate       │ → HTTP/HTTPS testing, 50 concurrent workers
└────────┬────────┘
         ↓
┌─────────────────┐
│  Export Files   │ → TXT, JSON, HTTP, HTTPS formats
└─────────────────┘
```

## Proxy Sources

Proxies are collected from 16+ free sources:

| Source | Type | API |
|--------|------|-----|
| ProxyScrape | API | ✓ |
| GeoNode | API | ✓ |
| TheSpeedX (GitHub) | List | ✓ |
| clarketm (GitHub) | List | ✓ |
| free-proxy-list.net | Scrape | - |
| proxy-list.download | API | ✓ |
| 站大爷 (zdaye) | Scrape | - |
| 66ip | Scrape | - |
| 开心代理 (kxdaili) | Scrape | - |
| 快代理 (kuaidaili) | Scrape | - |
| 云代理 (ip3366) | Scrape | - |
| 小幻代理 (ihuan) | Scrape | - |
| 89ip | Scrape | - |
| 稻壳代理 (docip) | API | ✓ |
| spys.one | Scrape | - |
| freeproxylists.net | Scrape | - |

## Validation

All proxies are validated against:

- **Format**: Must match `ip:port` or `username:password@ip:port`
- **HTTP Test**: Request to `http://httpbin.org/ip` (must return 200 OK)
- **HTTPS Test**: Request to `https://www.qq.com` (must return 200 OK)
- **Timeout**: 10 seconds per validation
- **Concurrency**: 50 parallel validators

## Configuration

Configure via environment variables:

```bash
# Logging
export LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR

# Concurrency
export MAX_FETCH_WORKERS=10        # Concurrent fetcher threads
export MAX_VALIDATION_WORKERS=50   # Concurrent validator threads

# Validation
export VALIDATION_TIMEOUT=10       # Seconds per validation test
export HTTP_TEST_URL=http://httpbin.org/ip
export HTTPS_TEST_URL=https://www.qq.com

# Run with custom config
python main.py
```

## GitHub Actions Setup

1. Fork this repository
2. Enable GitHub Actions in your fork
3. The workflow runs automatically:
   - Daily at 00:00 UTC
   - On push to main/master
   - Manual trigger via Actions tab

4. Proxies are published as GitHub Releases

### Workflow Features

- **Automatic Scheduling**: Daily cron job
- **Release Management**: Creates tagged releases with proxy files
- **Cleanup**: Keeps only the latest 30 releases
- **Summary**: Displays collection stats in workflow summary
- **Caching**: Pip dependencies cached for faster runs

## Output Files

| File | Format | Description |
|------|--------|-------------|
| `proxies.txt` | Plain text | All proxies (ip:port), one per line |
| `proxies.json` | JSON | All proxies with metadata (http/https support, source) |
| `http_proxies.txt` | Plain text | HTTP proxies with `http://` prefix |
| `https_proxies.txt` | Plain text | HTTPS-capable proxies with `https://` prefix |
| `README.md` | Markdown | Usage instructions and statistics |

### JSON Format

```json
{
  "count": 150,
  "updated_at": "2025-01-15 00:00:00 UTC",
  "proxies": [
    {
      "proxy": "1.2.3.4:8080",
      "http": true,
      "https": true,
      "source": "proxyscrape"
    }
  ]
}
```

## Comparison with Original

This is a **complete rewrite** optimized for GitHub Actions:

| Feature | Original | This Version |
|---------|----------|--------------|
| **Purpose** | Long-running service | GitHub Actions collector |
| **Dependencies** | 8 packages | 2 packages |
| **Database** | Redis required | In-memory only |
| **API Server** | Flask + Gunicorn | None (file export) |
| **Scheduler** | APScheduler | GitHub Actions |
| **Code Files** | ~30 files | 5 core files |
| **Lines of Code** | ~2000+ | ~800 |
| **Type Hints** | Partial | Complete |
| **Concurrency** | Manual threading | concurrent.futures |
| **Configuration** | Config file + DB | Environment variables |
| **Observability** | Custom logging | Python logging |

## Design Principles

Following the request for **Clear · Safe · Consistent · Observable · Maintainable** code:

### Clear
- Simple linear data flow
- Descriptive function and variable names
- Comprehensive docstrings
- Type hints throughout

### Safe
- Proper exception handling at all levels
- Timeout protection on all network requests
- SSL warning suppression (for proxy testing)
- Graceful handling of empty results

### Consistent
- PEP 8 style guide adherence
- Consistent error handling patterns
- Uniform logging format
- Standard library preferences (dataclasses, pathlib)

### Observable
- Structured logging with timestamps
- Progress tracking during validation
- Detailed statistics output
- GitHub Actions workflow summaries

### Maintainable
- Minimal dependencies (2 packages)
- Modular architecture (5 core modules)
- No external services required
- Well-documented configuration
- Type safety with mypy compatibility

## Performance

Typical collection stats:
- **Fetching**: 10-30 seconds (16 sources, 10 concurrent workers)
- **Validation**: 2-5 minutes (50 concurrent workers, depends on proxy count)
- **Total Runtime**: 3-10 minutes
- **Success Rate**: 5-20% of fetched proxies are valid

## Important Notes

⚠️ **Free Proxy Limitations**:
- Limited reliability (most fail within hours)
- Low success rates (5-20%)
- Frequent IP blocks and rate limiting
- Not suitable for production workloads
- No SLA or uptime guarantees

✅ **Best Practices**:
- Always implement retry logic
- Validate proxies before use
- Rotate through multiple proxies
- Consider paid proxy services for production
- Respect target website terms of service

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Areas for improvement:
- Additional proxy sources
- Better validation strategies
- Performance optimizations
- Documentation improvements

## Credits

This is a minimal rewrite of the excellent [proxy_pool](https://github.com/jhao104/proxy_pool) project by @jhao104, optimized specifically for GitHub Actions workflows.