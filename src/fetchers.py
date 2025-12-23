"""Proxy fetchers from various free sources."""

import re
import logging
import random
from typing import Iterator
from datetime import datetime
from time import sleep

import requests
from lxml import etree

from .config import USER_AGENTS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def get_headers() -> dict[str, str]:
    """Get random headers for requests."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    }


def safe_request(url: str, timeout: int = REQUEST_TIMEOUT, **kwargs) -> requests.Response | None:
    """Make a safe HTTP request with error handling."""
    try:
        response = requests.get(url, headers=get_headers(), timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.debug(f"Request failed for {url}: {e}")
        return None


def fetch_zdaye() -> Iterator[str]:
    """站大爷 https://www.zdaye.com/"""
    try:
        response = safe_request("https://www.zdaye.com/dayProxy.html", verify=False)
        if not response:
            return

        tree = etree.HTML(response.content)
        latest_time_str = tree.xpath("//span[@class='thread_time_info']/text()")
        if not latest_time_str:
            return

        latest_time = datetime.strptime(latest_time_str[0].strip(), "%Y/%m/%d %H:%M:%S")
        if (datetime.now() - latest_time).seconds >= 300:  # Only collect if updated within 5 minutes
            return

        page_url = tree.xpath("//h3[@class='thread_title']/a/@href")
        if not page_url:
            return

        target_url = f"https://www.zdaye.com/{page_url[0].strip()}"
        while target_url:
            page_response = safe_request(target_url, verify=False)
            if not page_response:
                break

            page_tree = etree.HTML(page_response.content)
            for tr in page_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                if ip and port:
                    yield f"{ip}:{port}"

            next_page = page_tree.xpath("//div[@class='page']/a[@title='下一页']/@href")
            target_url = f"https://www.zdaye.com/{next_page[0].strip()}" if next_page else None
            if target_url:
                sleep(2)
    except Exception as e:
        logger.debug(f"fetch_zdaye error: {e}")


def fetch_66ip() -> Iterator[str]:
    """代理66 http://www.66ip.cn/"""
    try:
        response = safe_request("http://www.66ip.cn/")
        if not response:
            return

        tree = etree.HTML(response.content)
        for i, tr in enumerate(tree.xpath("(//table)[3]//tr")):
            if i > 0:
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                if ip and port:
                    yield f"{ip}:{port}"
    except Exception as e:
        logger.debug(f"fetch_66ip error: {e}")


def fetch_kxdaili() -> Iterator[str]:
    """开心代理 http://www.kxdaili.com/"""
    urls = [
        "http://www.kxdaili.com/dailiip.html",
        "http://www.kxdaili.com/dailiip/2/1.html"
    ]
    for url in urls:
        try:
            response = safe_request(url)
            if not response:
                continue

            tree = etree.HTML(response.content)
            for tr in tree.xpath("//table[@class='active']//tr")[1:]:
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                if ip and port:
                    yield f"{ip}:{port}"
        except Exception as e:
            logger.debug(f"fetch_kxdaili error for {url}: {e}")


def fetch_freeproxylists() -> Iterator[str]:
    """FreeProxyLists https://www.freeproxylists.net/"""
    try:
        from urllib.parse import unquote

        response = safe_request(
            "https://www.freeproxylists.net/zh/?c=CN&pt=&pr=&a%5B%5D=0&a%5B%5D=1&a%5B%5D=2&u=50",
            verify=False
        )
        if not response:
            return

        tree = etree.HTML(response.content)
        for tr in tree.xpath("//tr[@class='Odd']") + tree.xpath("//tr[@class='Even']"):
            ip_script = "".join(tr.xpath("./td[1]/script/text()")).strip()
            port = "".join(tr.xpath("./td[2]/text()")).strip()

            if ip_script and port:
                ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', unquote(ip_script))
                if ips:
                    yield f"{ips[0]}:{port}"
    except Exception as e:
        logger.debug(f"fetch_freeproxylists error: {e}")


def fetch_kuaidaili() -> Iterator[str]:
    """快代理 https://www.kuaidaili.com/"""
    patterns = [
        "https://www.kuaidaili.com/free/inha/{}/",
        "https://www.kuaidaili.com/free/intr/{}/"
    ]

    for page in range(1, 2):  # Only first page to avoid rate limiting
        for pattern in patterns:
            try:
                url = pattern.format(page)
                response = safe_request(url)
                if not response:
                    continue

                tree = etree.HTML(response.content)
                for tr in tree.xpath(".//table//tr")[1:]:
                    cols = tr.xpath("./td/text()")
                    if len(cols) >= 2:
                        yield f"{cols[0]}:{cols[1]}"
                sleep(1)
            except Exception as e:
                logger.debug(f"fetch_kuaidaili error: {e}")


def fetch_ip3366() -> Iterator[str]:
    """云代理 http://www.ip3366.net/"""
    urls = ["http://www.ip3366.net/free/?stype=1", "http://www.ip3366.net/free/?stype=2"]
    for url in urls:
        try:
            response = safe_request(url)
            if not response:
                continue

            proxies = re.findall(
                r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>',
                response.text
            )
            for proxy in proxies:
                yield f"{proxy[0]}:{proxy[1]}"
        except Exception as e:
            logger.debug(f"fetch_ip3366 error: {e}")


def fetch_ihuan() -> Iterator[str]:
    """小幻代理 https://ip.ihuan.me/"""
    try:
        response = safe_request("https://ip.ihuan.me/address/5Lit5Zu9.html")
        if not response:
            return

        proxies = re.findall(
            r'>\s*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*?</a></td><td>(\d+)</td>',
            response.text
        )
        for proxy in proxies:
            yield f"{proxy[0]}:{proxy[1]}"
    except Exception as e:
        logger.debug(f"fetch_ihuan error: {e}")


def fetch_89ip() -> Iterator[str]:
    """89免费代理 https://www.89ip.cn/"""
    try:
        response = safe_request("https://www.89ip.cn/index_1.html")
        if not response:
            return

        proxies = re.findall(
            r'<td.*?>[\s\S]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s\S]*?</td>[\s\S]*?<td.*?>[\s\S]*?(\d+)[\s\S]*?</td>',
            response.text
        )
        for proxy in proxies:
            yield f"{proxy[0]}:{proxy[1]}"
    except Exception as e:
        logger.debug(f"fetch_89ip error: {e}")


def fetch_docip() -> Iterator[str]:
    """稻壳代理 https://www.docip.net/"""
    try:
        response = safe_request("https://www.docip.net/data/free.json")
        if not response:
            return

        data = response.json()
        if isinstance(data, dict) and "data" in data:
            for item in data["data"]:
                if isinstance(item, dict) and "ip" in item:
                    yield item["ip"]
    except Exception as e:
        logger.debug(f"fetch_docip error: {e}")


def fetch_proxyscrape() -> Iterator[str]:
    """ProxyScrape API https://api.proxyscrape.com/"""
    try:
        url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        response = safe_request(url, timeout=20)
        if not response:
            return

        for line in response.text.split('\n'):
            proxy = line.strip()
            if proxy and ':' in proxy:
                yield proxy
    except Exception as e:
        logger.debug(f"fetch_proxyscrape error: {e}")


def fetch_speedx() -> Iterator[str]:
    """GitHub TheSpeedX proxy list"""
    urls = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    ]
    for url in urls:
        try:
            response = safe_request(url, timeout=20)
            if not response:
                continue

            for line in response.text.split('\n'):
                proxy = line.strip()
                if proxy and ':' in proxy:
                    yield proxy
        except Exception as e:
            logger.debug(f"fetch_speedx error for {url}: {e}")


def fetch_freeproxylist() -> Iterator[str]:
    """free-proxy-list.net"""
    try:
        response = safe_request("https://free-proxy-list.net/")
        if not response:
            return

        tree = etree.HTML(response.content)
        for tr in tree.xpath("//table[@id='proxylisttable']//tr")[1:]:
            ip = "".join(tr.xpath("./td[1]/text()"))
            port = "".join(tr.xpath("./td[2]/text()"))
            if ip and port:
                yield f"{ip}:{port}"
    except Exception as e:
        logger.debug(f"fetch_freeproxylist error: {e}")


def fetch_proxylist_download() -> Iterator[str]:
    """proxy-list.download"""
    urls = [
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://www.proxy-list.download/api/v1/get?type=https",
    ]
    for url in urls:
        try:
            response = safe_request(url, timeout=20)
            if not response:
                continue

            for line in response.text.split('\n'):
                proxy = line.strip()
                if proxy and ':' in proxy:
                    yield proxy
        except Exception as e:
            logger.debug(f"fetch_proxylist_download error for {url}: {e}")


def fetch_geonode() -> Iterator[str]:
    """GeoNode Free Proxy API"""
    try:
        url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
        response = safe_request(url, timeout=20)
        if not response:
            return

        data = response.json()
        if isinstance(data, dict) and "data" in data:
            for proxy in data["data"]:
                ip = proxy.get("ip")
                port = proxy.get("port")
                if ip and port:
                    yield f"{ip}:{port}"
    except Exception as e:
        logger.debug(f"fetch_geonode error: {e}")


def fetch_spysone() -> Iterator[str]:
    """spys.one"""
    try:
        response = safe_request("http://spys.one/free-proxy-list/CN/")
        if not response:
            return

        tree = etree.HTML(response.content)
        if tree.xpath('//body'):
            body_text = tree.xpath('//body')[0].text_content()
            proxies = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', body_text)
            for proxy in proxies:
                yield f"{proxy[0]}:{proxy[1]}"
    except Exception as e:
        logger.debug(f"fetch_spysone error: {e}")


def fetch_clarketm() -> Iterator[str]:
    """GitHub clarketm proxy-list"""
    try:
        url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        response = safe_request(url, timeout=20)
        if not response:
            return

        for line in response.text.split('\n'):
            proxy = line.strip()
            if proxy and ':' in proxy and not proxy.startswith('#'):
                yield proxy
    except Exception as e:
        logger.debug(f"fetch_clarketm error: {e}")


# Registry of all fetcher functions
FETCHERS: dict[str, callable] = {
    "zdaye": fetch_zdaye,
    "66ip": fetch_66ip,
    "kxdaili": fetch_kxdaili,
    "freeproxylists": fetch_freeproxylists,
    "kuaidaili": fetch_kuaidaili,
    "ip3366": fetch_ip3366,
    "ihuan": fetch_ihuan,
    "89ip": fetch_89ip,
    "docip": fetch_docip,
    "proxyscrape": fetch_proxyscrape,
    "speedx": fetch_speedx,
    "freeproxylist": fetch_freeproxylist,
    "proxylist_download": fetch_proxylist_download,
    "geonode": fetch_geonode,
    "spysone": fetch_spysone,
    "clarketm": fetch_clarketm,
}
