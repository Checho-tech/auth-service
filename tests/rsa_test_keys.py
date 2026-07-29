"""Shared test helper: a throwaway RSA key pair for both test suites.

Never a fixed PEM string committed to the repo — a secret-scanner would
(rightly) flag a private key literal even if it's only ever used in tests.
Generating it fresh on each test run keeps this test-only and inert.
"""

import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_test_keypair() -> tuple[str, str]:
    """Returns (private_key_path, public_key_path) for a fresh RSA key pair."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="auth_service_test_keys_"))
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_path = tmp_dir / "private.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    public_path = tmp_dir / "public.pem"
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    return str(private_path), str(public_path)
