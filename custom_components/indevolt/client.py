# custom_components/indevolt/client.py
import asyncio
import async_timeout
import json
import logging
from typing import Any, List, Optional

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp

_LOGGER = logging.getLogger(__name__)
DEFAULT_PORT = 8080


class IndevoltAPIError(Exception):
    pass


class IndevoltClient:
    """Async client for Indevolt OpenData HTTP API (GetData / SetData)."""

    def __init__(self, hass, host: str, port: int = DEFAULT_PORT, username: Optional[str] = None, password: Optional[str] = None):
        self.hass = hass
        self._host = host
        self._port = port
        self._session = async_get_clientsession(hass)
        self._lock = asyncio.Lock()
        self._username = username
        self._password = password

    def _base_url(self) -> str:
        return f"http://{self._host}:{self._port}/rpc"

    async def _make_auth(self):
        if self._username and self._password:
            try:
                return aiohttp.DigestAuth(self._username, self._password)
            except Exception:
                _LOGGER.debug("DigestAuth failed; proceeding without auth")
        return None

    async def async_getdata(self, points: List[int], timeout: int = 8) -> dict:
        if not points:
            return {}
        params = {"t": points}
        url = f"{self._base_url()}/Indevolt.GetData?config={json.dumps(params)}"
        auth = await self._make_auth()
        async with async_timeout.timeout(timeout):
            async with self._lock:
                resp = await self._session.post(url, auth=auth)
                text = await resp.text()
                if resp.status >= 400:
                    raise IndevoltAPIError(f"GetData {resp.status}: {text}")
                try:
                    return await resp.json()
                except Exception:
                    _LOGGER.debug("GetData non-json response: %s", text)
                    return {}

    async def async_setdata(self, t: int, v: List[Any], timeout: int = 8) -> bool:
        config = {"f": 16, "t": t, "v": v}
        url = f"{self._base_url()}/Indevolt.SetData?config={json.dumps(config)}"
        auth = await self._make_auth()
        async with async_timeout.timeout(timeout):
            async with self._lock:
                resp = await self._session.post(url, auth=auth)
                text = await resp.text()
                if resp.status >= 400:
                    raise IndevoltAPIError(f"SetData {resp.status}: {text}")
                try:
                    j = await resp.json()
                    return bool(j.get("result", False))
                except Exception:
                    return "true" in text.lower()

    # Convenience wrappers
    async def async_set_mode(self, mode: int) -> bool:
        return await self.async_setdata(47005, [mode])

    async def async_set_state_power_soc(self, state: int, power: int, soc: int) -> bool:
        return await self.async_setdata(47015, [state, power, soc])
