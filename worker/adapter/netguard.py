"""Validation for user-supplied video URLs.

The URL ends up on a yt-dlp command line and makes the server open network
connections, so it must be (a) really an http(s) URL, (b) unable to be mistaken
for a command-line option, and (c) must not point at private/internal hosts
(SSRF) such as 127.0.0.1, 10.x.x.x or the cloud metadata server 169.254.169.254.

Residual risk: DNS can change between this check and yt-dlp's own lookup
(DNS rebinding), and redirects are followed by yt-dlp. Run the worker with no
credentials on its VM and a locked-down firewall (see deploy docs) as defence in depth.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlsplit

MAX_URL_LENGTH = 2000
_CONTROL = re.compile(r"[\x00-\x20\x7f]")


class UnsafeUrl(ValueError):
    """Raised with a message that is safe to show to the end user."""


def _is_public(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
                or addr.is_reserved or addr.is_unspecified
                or (addr.version == 6 and addr.ipv4_mapped is not None and not _is_public(str(addr.ipv4_mapped))))


def check_public_video_url(url: str) -> str:
    """Return the cleaned URL or raise UnsafeUrl."""
    url = (url or "").strip()
    if not url or len(url) > MAX_URL_LENGTH:
        raise UnsafeUrl("Enter a video link between 1 and 2000 characters.")
    if _CONTROL.search(url):
        raise UnsafeUrl("The link contains spaces or invalid characters.")
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise UnsafeUrl("Only http:// and https:// links are supported.")
    host = parts.hostname
    if not host:
        raise UnsafeUrl("The link has no host name.")
    if parts.username or parts.password:
        raise UnsafeUrl("Links containing a username or password are not supported.")
    try:
        infos = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80),
                                   type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrl("That link's host name could not be found.") from exc
    addresses = {info[4][0] for info in infos}
    if not addresses or not all(_is_public(a) for a in addresses):
        raise UnsafeUrl("That link points to a private or internal address, which is not allowed.")
    return url
