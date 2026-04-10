from dataclasses import dataclass
from typing import Any

from nitrado.http import NitrapiResponse


@dataclass(frozen=True, slots=True)
class ActivationResponse:
    success: bool

    @classmethod
    def from_nitrapi(cls, envelope: NitrapiResponse[Any]) -> 'ActivationResponse':
        return cls(success=envelope.status == 'success')
