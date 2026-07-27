"""Hashing helper for opaque/JWT tokens that must be stored at rest.

Unlike passwords, these tokens are high-entropy random strings, so a fast
hash (SHA-256) is enough — there's no brute-force risk the way there is
with human-chosen passwords, which is why this doesn't use bcrypt.
"""

import hashlib


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
