from dataclasses import dataclass
from typing import Any

from nitrado.http import NitradoHTTPError, NitrapiResponse


@dataclass(frozen=True, slots=True)
class RegistrationResponse:
    user_id: int
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    scopes: list[str]

    @classmethod
    def from_nitrapi(cls, envelope: NitrapiResponse[Any]) -> 'RegistrationResponse':
        raw = envelope.data
        if not isinstance(raw, dict):
            raise NitradoHTTPError('Registration response missing or invalid "data"')
        inner = raw.get('registration')
        if not isinstance(inner, dict):
            raise NitradoHTTPError('Registration response missing "data.registration"')

        user = inner.get('user')
        if not isinstance(user, dict):
            raise NitradoHTTPError('Registration response missing "data.registration.user"')

        user_id = user.get('id')
        if not isinstance(user_id, int):
            raise NitradoHTTPError('Registration response missing or invalid "data.registration.user.id"')

        access_token = inner.get('access_token')
        if not isinstance(access_token, str):
            raise NitradoHTTPError('Registration response missing or invalid "data.registration.access_token"')

        refresh_token = inner.get('refresh_token')
        if not isinstance(refresh_token, str):
            raise NitradoHTTPError('Registration response missing or invalid "data.registration.refresh_token"')

        token_type = inner.get('token_type')
        if not isinstance(token_type, str):
            raise NitradoHTTPError('Registration response missing or invalid "data.registration.token_type"')

        expires_in = inner.get('expires_in')
        if not isinstance(expires_in, int):
            raise NitradoHTTPError('Registration response missing or invalid "data.registration.expires_in"')

        scope = inner.get('scope')
        if not isinstance(scope, str):
            raise NitradoHTTPError('Registration response missing or invalid "data.registration.scope"')

        return cls(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            expires_in=expires_in,
            scopes=scope.split(),
        )
