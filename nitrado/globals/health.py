from dataclasses import dataclass
from typing import Any

from ..http import NitradoHTTPError, NitrapiResponse


@dataclass(frozen=True, slots=True)
class HealthResponse:
    status: str
    message: str

    @classmethod
    def from_nitrapi(cls, envelope: 'NitrapiResponse[Any]') -> 'HealthResponse':
        if envelope.message is None:
            raise NitradoHTTPError('Ping response missing "message"')
            
        return cls(status=envelope.status, message=envelope.message)