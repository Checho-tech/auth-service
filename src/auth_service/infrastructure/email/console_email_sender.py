"""Mock email sender: logs the message instead of hitting a real SMTP server.

Satisfies the "email verification (mock SMTP accepted)" requirement without
needing real credentials for a portfolio project. Swapping this for a real
provider (SES, SendGrid, Postmark) later only requires a new class that
implements IEmailSender — nothing in AuthService changes.
"""

import structlog

logger = structlog.get_logger()


class ConsoleEmailSender:
    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("mock_email_sent", to=to, subject=subject, body=body)
