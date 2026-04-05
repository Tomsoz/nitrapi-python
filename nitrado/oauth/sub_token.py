from dataclasses import dataclass
from typing import Any

from nitrado.http import NitradoHTTPError, NitrapiResponse


@dataclass(frozen=True, slots=True)
class SubToken:
    token: str
    token_type: str
    expires_in: int
    scopes: list[str]

    @classmethod
    def from_nitrapi(cls, envelope: 'NitrapiResponse[Any]') -> 'SubToken':
        raw = envelope.data
        if not isinstance(raw, dict):
            raise NitradoHTTPError('Subtoken response missing or invalid "data"')
        inner = raw.get('token')
        if not isinstance(inner, dict):
            raise NitradoHTTPError('Subtoken response missing "data.token"')
            
        return cls(
            token=inner.get("token"),
            token_type=inner.get("token_type"),
            expires_in=inner.get("expires_in"),
            scopes=inner.get("scopes", "").split(" ")
        )