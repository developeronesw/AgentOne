"""Target URL checks. Revalidate every redirect; reject private and non-global addresses."""
from __future__ import annotations
import ipaddress, socket
from urllib.parse import urlsplit, urlunsplit

def normalize_url(value: str) -> str:
    p = urlsplit(value.strip())
    if p.scheme.lower() not in {"http", "https"} or not p.hostname:
        raise ValueError("Enter a valid http or https website URL.")
    if p.username or p.password:
        raise ValueError("URLs containing credentials are not allowed.")
    host = p.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Local hostnames are not permitted.")
    try:
        port = p.port
    except ValueError as exc:
        raise ValueError("Invalid port number.") from exc
    if port is not None and port not in {80, 443}:
        raise ValueError("Only standard HTTP/HTTPS ports are permitted.")
    netloc = host if port is None else f"{host}:{port}"
    if ":" in host and not host.startswith("["): netloc = f"[{host}]" + (f":{port}" if port else "")
    return urlunsplit((p.scheme.lower(), netloc, p.path or "/", p.query, ""))

def validate_public_host(host: str) -> None:
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("Hostname could not be resolved.") from exc
        addresses = {ipaddress.ip_address(r[4][0]) for r in records}
    if not addresses or any(not ip.is_global for ip in addresses):
        raise ValueError("Crawl target resolves to a non-public IP address.")

def safe_target(url: str) -> str:
    value = normalize_url(url)
    host = urlsplit(value).hostname
    if not host: raise ValueError("URL hostname is missing.")
    validate_public_host(host)
    return value
