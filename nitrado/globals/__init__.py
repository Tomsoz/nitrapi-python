"""Unauthenticated Nitrapi endpoints and their response types."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from .health import HealthResponse
from .version import APIVersion

if TYPE_CHECKING:
    from .maintenance import MaintenanceResponse

__all__ = [
    'Global',
    'MaintenanceResponse',
    'HealthResponse',
    'APIVersion',
]


def __getattr__(name: str) -> Any:
    if name in ('MaintenanceData', 'MaintenanceFlags', 'MaintenanceResponse'):
        from . import maintenance as _maintenance

        return getattr(_maintenance, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


class Global:
    """Public (unauthenticated) Nitrapi endpoints.

    Each method opens its own :class:`~nitrado.http.HTTPClient` for that call.

    For bearer-token routes, use :class:`~nitrado.client.Client` instead.
    """

    @classmethod
    async def health(cls) -> HealthResponse:
        from ..http import HTTPClient

        async with HTTPClient() as client:
            return await client.health()

    @classmethod
    async def maintenance(cls) -> MaintenanceResponse:
        from ..http import HTTPClient

        async with HTTPClient() as client:
            return await client.maintenance()

    @classmethod
    async def version(cls) -> APIVersion:
        from ..http import HTTPClient

        async with HTTPClient() as client:
            return await client.version()
