"""Unauthenticated Nitrapi endpoints and response types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .health import HealthResponse
from .version import APIVersion

if TYPE_CHECKING:
    from ..http import HTTPClient
    from .maintenance import MaintenanceResponse

__all__ = [
    'Global',
    'GlobalAPI',
    'MaintenanceResponse',
    'HealthResponse',
    'APIVersion',
]


def __getattr__(name: str) -> Any:
    if name in ('MaintenanceData', 'MaintenanceFlags', 'MaintenanceResponse'):
        from . import maintenance as _maintenance

        return getattr(_maintenance, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


class GlobalAPI:
    """Public (unauthenticated) Nitrapi endpoints bound to one HTTP transport."""

    __slots__ = ('_http',)

    def __init__(self, http: 'HTTPClient') -> None:
        self._http = http

    async def health(self) -> HealthResponse:
        return HealthResponse.from_nitrapi(await self._http.request(Route('GET', '/ping')))

    async def maintenance(self) -> MaintenanceResponse:
        return MaintenanceResponse.from_nitrapi(await self._http.request(Route('GET', '/maintenance')))

    async def version(self) -> APIVersion:
        return APIVersion.from_nitrapi(await self._http.request(Route('GET', '/version')))


class Global:
    """One-shot convenience wrapper for public Nitrapi endpoints.

    For connection reuse and shared rate-limit state, prefer
    ``Nitrado().globals`` over these class methods.
    """

    @classmethod
    async def health(cls) -> HealthResponse:
        from ..http import HTTPClient

        async with HTTPClient() as http:
            return await http.globals.health()

    @classmethod
    async def maintenance(cls) -> MaintenanceResponse:
        from ..http import HTTPClient

        async with HTTPClient() as http:
            return await http.globals.maintenance()

    @classmethod
    async def version(cls) -> APIVersion:
        from ..http import HTTPClient

        async with HTTPClient() as http:
            return await http.globals.version()


from ..http import Route
