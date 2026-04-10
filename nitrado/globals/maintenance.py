"""DTOs for ``GET /maintenance`` (global / unauthenticated)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..http import NitradoHTTPError, NitrapiResponse

@dataclass(frozen=True, slots=True)
class MaintenanceResponse:
    cloud_backend: bool
    domain_backend: bool
    dns_backend: bool
    pmacct_backend: bool

    @classmethod
    def from_nitrapi(cls, envelope: NitrapiResponse[Any]) -> MaintenanceResponse:
        raw = envelope.data
        if not isinstance(raw, dict):
            raise NitradoHTTPError('Maintenance response missing or invalid "data"')
        inner = raw.get('maintenance')
        if not isinstance(inner, dict):
            raise NitradoHTTPError('Maintenance response missing "data.maintenance"')

        cloud_backend = inner.get('cloud_backend')
        if not isinstance(cloud_backend, bool):
            raise NitradoHTTPError('Maintenance response missing or invalid "data.maintenance.cloud_backend"')

        domain_backend = inner.get('domain_backend')
        if not isinstance(domain_backend, bool):
            raise NitradoHTTPError('Maintenance response missing or invalid "data.maintenance.domain_backend"')

        dns_backend = inner.get('dns_backend')
        if not isinstance(dns_backend, bool):
            raise NitradoHTTPError('Maintenance response missing or invalid "data.maintenance.dns_backend"')

        pmacct_backend = inner.get('pmacct_backend')
        if not isinstance(pmacct_backend, bool):
            raise NitradoHTTPError('Maintenance response missing or invalid "data.maintenance.pmacct_backend"')

        return cls(
            cloud_backend=cloud_backend,
            domain_backend=domain_backend,
            dns_backend=dns_backend,
            pmacct_backend=pmacct_backend,
        )
