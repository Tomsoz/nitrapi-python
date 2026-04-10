from dataclasses import dataclass
from typing import Any

from nitrado.http import NitradoHTTPError, NitrapiResponse


@dataclass(frozen=True, slots=True)
class RecaptchaResponse:
    enabled: bool
    key: str

    @classmethod
    def from_nitrapi(cls, envelope: NitrapiResponse[Any]) -> 'RecaptchaResponse':
        raw = envelope.data
        if not isinstance(raw, dict):
            raise NitradoHTTPError('Recaptcha response missing or invalid "data"')
        recaptcha = raw.get('google_recaptcha')
        if not isinstance(recaptcha, dict):
            raise NitradoHTTPError('Recaptcha response missing "data.google_recaptcha"')

        enabled = recaptcha.get('enabled')
        if not isinstance(enabled, bool):
            raise NitradoHTTPError('Recaptcha response missing or invalid "data.google_recaptcha.enabled"')

        key = recaptcha.get('key')
        if not isinstance(key, str):
            raise NitradoHTTPError('Recaptcha response missing or invalid "data.google_recaptcha.key"')

        return cls(enabled=enabled, key=key)
