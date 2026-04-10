import asyncio
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from nitrado import Nitrado

# Registration app credentials.
CLIENT_ID = 'your-client-id'
CLIENT_SECRET = 'your-client-secret'

# Account details to create.
USERNAME = 'your-username'
EMAIL = 'you@example.com'
PASSWORD = 'your-password'
CURRENCY = 'EUR'
LANGUAGE = 'deu'
TIMEZONE = 'Europe/Berlin'
CONSENT_NEWSLETTER = False


def _parse_activation_input(raw: str) -> tuple[str, str | None]:
    text = raw.strip()
    if not text:
        return '', None
    if '://' not in text:
        return text, None

    parsed = urlparse(text)
    query = parse_qs(parsed.query)
    code = query.get('code', [''])[0].strip()
    uuid = query.get('uuid', [''])[0].strip()
    return code, uuid or None


async def main() -> None:
    client = Nitrado()
    try:
        recaptcha_token: str | None = None
        recaptcha = await client.registration.recaptcha()

        if recaptcha.enabled:
            print('reCAPTCHA is enabled for registration.')
            print(f'Site key: {recaptcha.key}')
            recaptcha_token = input('Paste the solved reCAPTCHA token: ').strip() or None

        registration = await client.registration.register(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            recaptcha=recaptcha_token,
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD,
            currency=CURRENCY,
            language=LANGUAGE,
            timezone=TIMEZONE,
            consent_newsletter=CONSENT_NEWSLETTER,
        )

        print('Account created successfully.')
        print(f'User ID: {registration.user_id}')
        print(f'Access token: {registration.access_token}')
        print(f'Refresh token: {registration.refresh_token}')
        print('Check your email for the activation link or code.')

        activation_input = input('Paste the activation URL or code from the email: ').strip()
        code, uuid = _parse_activation_input(activation_input)

        if not code:
            raise ValueError('Activation code is required.')
        if not uuid:
            uuid = input('Paste the activation UUID from the email or activation URL: ').strip()
        if not uuid:
            raise ValueError('Activation UUID is required.')

        activation = await client.registration.activate(code=code, uuid=uuid)
        print(f'Activation successful: {activation.success}')
    finally:
        await client.close()


if __name__ == '__main__':
    asyncio.run(main())
