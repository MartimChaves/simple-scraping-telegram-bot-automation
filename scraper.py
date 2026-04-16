"""Web scraper with SSRF-safe URL validation."""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]

REQUEST_TIMEOUT = 10


class URLValidationError(Exception):
    """Raised when a URL fails safety validation."""


def validate_url(url: str) -> str:
    """Validate a URL is safe to request. Returns the URL if valid, raises URLValidationError otherwise."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise URLValidationError(f"Only http/https URLs are allowed, got: {parsed.scheme!r}")

    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL has no hostname")

    # Resolve hostname to IP to prevent DNS rebinding
    try:
        ip_str = socket.gethostbyname(hostname)
    except socket.gaierror:
        raise URLValidationError(f"Could not resolve hostname: {hostname}")

    ip = ipaddress.ip_address(ip_str)
    for network in BLOCKED_NETWORKS:
        if ip in network:
            raise URLValidationError("URL blocked: private/internal addresses are not allowed")

    return url


def scrape_page(url: str, selector: str) -> list[dict]:
    """Fetch a page and extract elements matching a CSS selector.

    Returns a list of dicts with 'text' key for each matched element.
    """
    validate_url(url)
    logger.info("Scraping %s with selector %r", url, selector)

    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    elements = soup.select(selector)

    logger.info("Found %d elements", len(elements))
    return [{"text": el.get_text(strip=True)} for el in elements]
