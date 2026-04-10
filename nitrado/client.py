from __future__ import annotations

from .http import HTTPClient


class Nitrado(HTTPClient):
    """Primary Nitrapi client.

    Use this for a reusable client instance with grouped APIs such as
    ``client.globals`` and ``client.registration``.
    """


NitradoClient = Nitrado


class Client:
    """Authenticated Nitrapi API access.

    Instance methods are for routes that require a bearer token. Pass the same
    :class:`Nitrado` instance you use for the app lifetime; this object sets
    ``client.token`` for you.

    Unauthenticated endpoints belong on :class:`~nitrado.globals.Global` instead.
    """

    __slots__ = ('_client', '_token')

    def __init__(self, client: HTTPClient, token: str) -> None:
        self._client = client
        self._token = token
        client.token = token

    @property
    def http(self) -> HTTPClient:
        return self._client

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value
        self._client.token = value

    # Authenticated routes: add instance methods here, e.g.
    # async def servers(self) -> NitrapiResponse[...]:
    #     return await self._client.request(Route('GET', '/user/...'))
