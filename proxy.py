from aiohttp_socks import ProxyConnector
from aiogram.client.session.aiohttp import AiohttpSession
import os

def get_proxy_session():
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        connector = ProxyConnector.from_url(proxy_url)
        return AiohttpSession(connector=connector)
    return None