import socket

import pytest

from adapter.netguard import UnsafeUrl, check_public_video_url


@pytest.mark.parametrize("url", [
    "--exec=touch /tmp/pwned",
    "-o /etc/passwd",
    "file:///etc/passwd",
    "ftp://example.com/v.mp4",
    "javascript:alert(1)",
    "https://user:pw@example.com/v",
    "https://exa mple.com/v",
    "https://",
    "",
    "   ",
    "http://127.0.0.1:8000/health",
    "http://localhost/admin",
    "http://169.254.169.254/computeMetadata/v1/",
    "http://10.0.0.5/video.mp4",
    "http://192.168.1.1/",
    "http://[::1]/",
    "http://[::ffff:127.0.0.1]/",
    "http://0.0.0.0/",
    "https://example.com/" + "a" * 2100,
])
def test_rejects_unsafe_urls(url):
    with pytest.raises(UnsafeUrl):
        check_public_video_url(url)


def test_accepts_public_ip_literal():
    assert check_public_video_url(" https://8.8.8.8/watch?v=abc ") == "https://8.8.8.8/watch?v=abc"


def test_hostname_resolving_to_private_ip_is_rejected(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("10.1.2.3", 443))])
    with pytest.raises(UnsafeUrl):
        check_public_video_url("https://innocent.example/v")


def test_mixed_public_and_private_resolution_is_rejected(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [
        (2, 1, 6, "", ("8.8.8.8", 443)), (2, 1, 6, "", ("169.254.169.254", 443))])
    with pytest.raises(UnsafeUrl):
        check_public_video_url("https://rebind.example/v")


def test_hostname_resolving_publicly_is_accepted(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    assert check_public_video_url("https://example.com/v") == "https://example.com/v"
