from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generic, Mapping, Optional, TypeVar

import aiohttp
from aiohttp import ClientResponse
from urllib.parse import quote

TData = TypeVar('TData')

if TYPE_CHECKING:
    from .globals import GlobalAPI
    from .registration import RegistrationAPI

class NitradoRateLimitExceeded(Exception):
    """Raised when the API keeps returning HTTP 429 after automatic backoff."""

    def __init__(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
        reset_epoch: Optional[float] = None,
    ) -> None:
        super().__init__(message)
        self.limit = limit
        self.reset_epoch = reset_epoch


class NitradoHTTPError(Exception):
    """Raised for non-success Nitrapi JSON responses or unexpected HTTP status."""

    def __init__(self, message: str, *, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True, slots=True)
class NitrapiResponse(Generic[TData]):
    status: str
    message: Optional[str] = None
    data: Optional[TData] = None

    @classmethod
    def from_payload(cls, raw: Any, *, http_status: Optional[int] = None) -> 'NitrapiResponse[Any]':
        if not isinstance(raw, dict):
            raise NitradoHTTPError(
                'Expected a JSON object body from Nitrapi',
                status=http_status,
            )
        status = raw.get('status')
        if not isinstance(status, str):
            raise NitradoHTTPError(
                'Nitrapi response has missing or invalid "status"',
                status=http_status,
            )
        message_raw = raw.get('message')
        message = str(message_raw) if message_raw is not None else None
        data = raw['data'] if 'data' in raw else None
        return cls(status=status, message=message, data=data)


# Shorthand for annotations, e.g. ``Response[MyDto]``.
Response = NitrapiResponse


class Route:
    BASE: ClassVar[str] = 'https://api.nitrado.net'

    def __init__(self, method: str, path: str, **parameters: Any) -> None:
        self.method: str = method.upper()
        self.path: str = path

        base = parameters.pop('base', self.BASE)
        url = base + self.path
        if parameters:
            url = url.format_map(
                {k: quote(v, safe='') if isinstance(v, str) else v for k, v in parameters.items()}
            )
        self.url: str = url


def _header_int(headers: Mapping[str, str], name: str) -> Optional[int]:
    raw = headers.get(name)
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _header_float(headers: Mapping[str, str], name: str) -> Optional[float]:
    raw = headers.get(name)
    if raw is None:
        return None
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _retry_after_seconds(headers: Mapping[str, str]) -> Optional[float]:
    raw = headers.get('Retry-After')
    if raw is None:
        return None
    try:
        return max(0.0, float(str(raw).strip()))
    except ValueError:
        return None


class HTTPClient:
    """Async Nitrapi HTTP client with Nitrado rate-limit handling.

    Uses ``X-RateLimit-Limit``, ``X-RateLimit-Remaining``, and ``X-RateLimit-Reset``
    (Unix timestamp) as described in the Nitrapi documentation and reference SDK.
    Requests are serialized so concurrent tasks do not burst past the hourly quota.
    """

    _RESET_BUFFER_S = 0.25

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        user_agent = 'Nitrapi-Python Python/{0.major}.{0.minor} aiohttp/{1}'
        self.user_agent = user_agent.format(sys.version_info, aiohttp.__version__)

        self.token: Optional[str] = None
        self._globals_api: Optional['GlobalAPI'] = None
        self._registration_api: Optional['RegistrationAPI'] = None

        self._request_lock = asyncio.Lock()
        self._rate_limit_limit: Optional[int] = None
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset_epoch: Optional[float] = None

    @property
    def globals(self) -> 'GlobalAPI':
        if self._globals_api is None:
            from .globals import GlobalAPI

            self._globals_api = GlobalAPI(self)
        return self._globals_api

    @property
    def registration(self) -> 'RegistrationAPI':
        if self._registration_api is None:
            from .registration import RegistrationAPI

            self._registration_api = RegistrationAPI(self)
        return self._registration_api

    @property
    def rate_limit_limit(self) -> Optional[int]:
        return self._rate_limit_limit

    @property
    def rate_limit_remaining(self) -> Optional[int]:
        return self._rate_limit_remaining

    @property
    def rate_limit_reset_epoch(self) -> Optional[float]:
        return self._rate_limit_reset_epoch

    def _apply_rate_limit_headers(self, headers: Mapping[str, str]) -> None:
        if not headers.get('X-RateLimit-Limit'):
            self._rate_limit_limit = None
            self._rate_limit_remaining = None
            self._rate_limit_reset_epoch = None
            return
        limit = _header_int(headers, 'X-RateLimit-Limit')
        remaining = _header_int(headers, 'X-RateLimit-Remaining')
        reset = _header_float(headers, 'X-RateLimit-Reset')
        if limit is not None:
            self._rate_limit_limit = limit
        if remaining is not None:
            self._rate_limit_remaining = remaining
        if reset is not None:
            self._rate_limit_reset_epoch = reset

    async def _sleep_until_reset(self, headers: Mapping[str, str]) -> None:
        reset_epoch = _header_float(headers, 'X-RateLimit-Reset') or self._rate_limit_reset_epoch
        delay: Optional[float] = None
        if reset_epoch is not None:
            delay = max(0.0, reset_epoch - time.time() + self._RESET_BUFFER_S)
        if delay is None or delay <= 0:
            delay = _retry_after_seconds(headers)
        if delay is None or delay <= 0:
            delay = 60.0
        await asyncio.sleep(delay)

    async def _respect_bucket_before_request(self) -> None:
        if self._rate_limit_remaining is None:
            return
        if self._rate_limit_remaining > 0:
            return
        if self._rate_limit_reset_epoch is None:
            return
        delay = self._rate_limit_reset_epoch - time.time() + self._RESET_BUFFER_S
        if delay > 0:
            await asyncio.sleep(delay)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def __aenter__(self) -> 'HTTPClient':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    @staticmethod
    async def _load_response_body(resp: ClientResponse) -> Any:
        data = await resp.read()
        ctype = resp.headers.get('Content-Type', '')
        if 'application/json' in ctype:
            if not data:
                return None
            try:
                return json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                return data.decode('utf-8', errors='replace')
        return data.decode('utf-8', errors='replace') if data else ''

    async def request(
        self,
        route: Route,
        *,
        json: Any = None,
        data: Any = None,
        params: Any = None,
        max_rate_limit_retries: int = 5,
    ) -> 'NitrapiResponse[Any]':
        """Perform an HTTP request and return a parsed :class:`NitrapiResponse` envelope.

        Handles 429 by sleeping until ``X-RateLimit-Reset`` (or ``Retry-After``) and
        retrying. Nitrapi error payloads (``status: error``) raise :class:`NitradoHTTPError`.
        """
        async with self._request_lock:
            await self._respect_bucket_before_request()

            headers: Dict[str, str] = {'User-Agent': self.user_agent}
            if self.token is not None:
                headers['Authorization'] = 'Bearer ' + self.token

            attempt = 0
            while True:
                session = await self._ensure_session()
                async with session.request(
                    route.method,
                    route.url,
                    headers=headers,
                    json=json,
                    data=data,
                    params=params,
                ) as resp:
                    self._apply_rate_limit_headers(resp.headers)

                    if resp.status == 429:
                        attempt += 1
                        if attempt > max_rate_limit_retries:
                            raise NitradoRateLimitExceeded(
                                'Rate limit exceeded; retries exhausted.',
                                limit=self._rate_limit_limit,
                                reset_epoch=self._rate_limit_reset_epoch,
                            )
                        await self._sleep_until_reset(resp.headers)
                        continue

                    body = await self._load_response_body(resp)

                    if isinstance(body, dict) and body.get('status') == 'error':
                        msg = str(body.get('message', 'Unknown API error'))
                        raise NitradoHTTPError(msg, status=resp.status)

                    if resp.status >= 400:
                        if isinstance(body, dict) and 'message' in body:
                            msg = str(body['message'])
                        else:
                            msg = resp.reason or f'HTTP {resp.status}'
                        raise NitradoHTTPError(msg, status=resp.status)

                    return NitrapiResponse.from_payload(body, http_status=resp.status)

    # Backward-compatible shortcuts. Prefer grouped APIs like ``http.globals.version()``
    # and ``http.registration.register()`` for better organization.
    async def health(self) -> Any:
        return await self.globals.health()

    async def maintenance(self) -> Any:
        return await self.globals.maintenance()

    async def version(self) -> Any:
        return await self.globals.version()

    async def register(
        self,
        client_id: str,
        client_secret: str,
        recaptcha: Optional[str],
        username: Optional[str],
        email: str,
        password: str,
        currency: str = 'EUR',
        language: str = 'deu',
        timezone: str = 'Europe/Berlin',
        consent_newsletter: bool = False,
    ) -> Any:
        return await self.registration.register(
            client_id=client_id,
            client_secret=client_secret,
            recaptcha=recaptcha,
            username=username,
            email=email,
            password=password,
            currency=currency,
            language=language,
            timezone=timezone,
            consent_newsletter=consent_newsletter,
        )

    async def activate(self, code: str, uuid: str) -> Any:
        return await self.registration.activate(code=code, uuid=uuid)

    async def recaptcha(self) -> Any:
        return await self.registration.recaptcha()
