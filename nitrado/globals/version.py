from dataclasses import dataclass
from typing import Any

from ..http import NitradoHTTPError, NitrapiResponse


@dataclass(frozen=True, slots=True)
class APIVersion:
    version: str

    @classmethod
    def from_nitrapi(cls, envelope: 'NitrapiResponse[Any]') -> 'APIVersion':
        if envelope.message is None:
            raise NitradoHTTPError('Version response missing "message"')
        return cls(version=envelope.message)