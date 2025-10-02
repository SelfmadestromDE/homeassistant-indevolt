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
        # Try to provide aiohttp DigestAuth if username/password available.
        if self._username and self._password:
            # aiohttp has aiohttp.DigestAuth class
            try:
                return aiohttp.DigestAuth(self._username, self._password)
            except Exception:
                _LOGGER.debug("DigestAuth not available or failed; proceeding without auth")
                return None
        return None

    async def async_getdata(self, points: List[int], timeout: int = 8) -> dict:
        """Call Indevolt.GetData for given cJson points. Returns dict (strings keys)."""
        if not points:
            return {}
        params = {"t": points}
        url = f"{self._base_url()}/Indevolt.GetData?config={json.dumps(params)}"
        auth = await self._make_auth()
        async with async_timeout.timeout(timeout):
            async with self._lock:
                try:
                    resp = await self._session.post(url, auth=auth)
                    text = await resp.text()
                    if resp.status >= 400:
                        _LOGGER.debug("GetData error %s %s", resp.status, text)
                        raise IndevoltAPIError(f"GetData {resp.status}: {text}")
                    try:
                        return await resp.json()
                    except Exception:
                        # sometimes returns plain text
                        _LOGGER.debug("GetData non-json response: %s", text)
                        return {}
                except asyncio.TimeoutError as err:
                    raise IndevoltAPIError("GetData timeout") from err
                except aiohttp.ClientError as err:
                    raise IndevoltAPIError("GetData connection error") from err

    async def async_setdata(self, t: int, v: List[Any], timeout: int = 8) -> bool:
        """
        Call Indevolt.SetData with f=16 default (per PDF).
        t: register address
        v: list of values
        """
        config = {"f": 16, "t": t, "v": v}
        url = f"{self._base_url()}/Indevolt.SetData?config={json.dumps(config)}"
        auth = await self._make_auth()
        async with async_timeout.timeout(timeout):
            async with self._lock:
                try:
                    resp = await self._session.post(url, auth=auth)
                    text = await resp.text()
                    if resp.status >= 400:
                        _LOGGER.debug("SetData error %s %s", resp.status, text)
                        raise IndevoltAPIError(f"SetData {resp.status}: {text}")
                    try:
                        j = await resp.json()
                        return bool(j.get("result", False))
                    except Exception:
                        _LOGGER.debug("SetData non-json response: %s", text)
                        # if not JSON, fallback by checking "true" substring
                        return "true" in text.lower()
                except asyncio.TimeoutError as err:
                    raise IndevoltAPIError("SetData timeout") from err
                except aiohttp.ClientError as err:
                    raise IndevoltAPIError("SetData connection error") from err

    # convenience wrappers (use these in entities)
    async def async_set_mode(self, mode: int) -> bool:
        # 47005 = Mode register per PDF
        return await self.async_setdata(47005, [mode])

    async def async_set_state_power_soc(self, state: int, power: int, soc: int) -> bool:
        # 47015 = state, 47016 = power, 47017 = soc -> But PDF shows an example writing t=47015 v=[2,700,5]
        # Use 47015 with v = [state, power, soc] as shown in the doc.
        return await self.async_setdata(47015, [state, power, soc])
