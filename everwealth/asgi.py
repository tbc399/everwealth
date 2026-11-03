"""Production ASGI entry point with trusted reverse-proxy headers."""

import os

from granian.utils.proxies import wrap_asgi_with_proxy_headers

from everwealth.main import app


def create_app():
    trusted_hosts = [
        host.strip()
        for host in os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1").split(",")
        if host.strip()
    ]
    return wrap_asgi_with_proxy_headers(app, trusted_hosts=trusted_hosts)
