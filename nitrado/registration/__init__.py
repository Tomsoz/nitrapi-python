"""Registration endpoints and response types."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http import HTTPClient
    from .activate import ActivationResponse
    from .recaptcha import RecaptchaResponse
    from .register import RegistrationResponse

__all__ = [
    'Registration',
    'RegistrationAPI',
    'RegistrationResponse',
    'ActivationResponse',
    'RecaptchaResponse',
]


class RegistrationAPI:
    """Registration endpoints bound to one HTTP transport."""

    __slots__ = ('_http',)

    def __init__(self, http: 'HTTPClient') -> None:
        self._http = http

    async def register(
        self,
        client_id: str,
        client_secret: str,
        recaptcha: str | None,
        username: str | None,
        email: str,
        password: str,
        currency: str = 'EUR',
        language: str = 'deu',
        timezone: str = 'Europe/Berlin',
        consent_newsletter: bool = False,
    ) -> RegistrationResponse:
        return RegistrationResponse.from_nitrapi(
            await self._http.request(
                Route('POST', '/registration', base='https://oauth.nitrado.net'),
                json={
                    'data': {
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'recaptcha': recaptcha,
                        'username': username,
                        'email': email,
                        'password': password,
                        'currency': currency,
                        'language': language,
                        'timezone': timezone,
                        'consent_newsletter': consent_newsletter,
                    }
                },
            )
        )

    async def activate(self, code: str, uuid: str) -> ActivationResponse:
        return ActivationResponse.from_nitrapi(
            await self._http.request(
                Route('GET', '/activation', base='https://oauth.nitrado.net'),
                params={
                    'code': code,
                    'uuid': uuid,
                },
            )
        )

    async def recaptcha(self) -> RecaptchaResponse:
        return RecaptchaResponse.from_nitrapi(
            await self._http.request(Route('GET', '/recaptcha', base='https://oauth.nitrado.net'))
        )


class Registration:
    """One-shot convenience wrapper for registration endpoints.

    For connection reuse and shared rate-limit state, prefer
    ``Nitrado().registration`` over these class methods.
    """

    @classmethod
    async def register(
        cls,
        client_id: str,
        client_secret: str,
        recaptcha: str | None,
        username: str | None,
        email: str,
        password: str,
        currency: str = 'EUR',
        language: str = 'deu',
        timezone: str = 'Europe/Berlin',
        consent_newsletter: bool = False,
    ) -> RegistrationResponse:
        from ..http import HTTPClient

        async with HTTPClient() as http:
            return await http.registration.register(
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

    @classmethod
    async def activate(cls, code: str, uuid: str) -> ActivationResponse:
        from ..http import HTTPClient

        async with HTTPClient() as http:
            return await http.registration.activate(code=code, uuid=uuid)

    @classmethod
    async def recaptcha(cls) -> RecaptchaResponse:
        from ..http import HTTPClient

        async with HTTPClient() as http:
            return await http.registration.recaptcha()


from ..http import Route
from .activate import ActivationResponse
from .recaptcha import RecaptchaResponse
from .register import RegistrationResponse