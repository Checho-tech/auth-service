"""Abstract contract for sending transactional emails (verification, password reset)."""

from typing import Protocol


class IEmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...
