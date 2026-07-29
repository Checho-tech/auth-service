"""Builds the JWKS (JSON Web Key Set) response from the RSA public key.

This is the standard, framework-agnostic format (RFC 7517) that any client
library — including PyJWT's own `PyJWKClient`, or Auth0/Okta SDKs — knows
how to parse. Publishing it here means Inventory Service (or any future
consumer) never needs a copy of the key file at all: it just points a
`PyJWKClient` at this URL and lets it fetch and cache the key.
"""

import base64
from typing import Any

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from auth_service.infrastructure.config import Settings


def _int_to_base64url(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    raw_bytes = value.to_bytes(length, byteorder="big")
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("ascii")


def build_jwks(settings: Settings) -> dict[str, Any]:
    public_key = load_pem_public_key(settings.jwt_public_key.encode())
    if not isinstance(public_key, RSAPublicKey):
        raise TypeError("JWT_PUBLIC_KEY_PATH must point to an RSA public key.")

    numbers = public_key.public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": settings.jwt_algorithm,
                "kid": settings.jwt_key_id,
                "n": _int_to_base64url(numbers.n),
                "e": _int_to_base64url(numbers.e),
            }
        ]
    }
