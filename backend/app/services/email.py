import smtplib
from email.message import EmailMessage

from app.core.config import Settings


class EmailDeliveryError(Exception):
    """Raised when an email cannot be delivered through the configured SMTP server."""


def send_email(
    settings: Settings,
    *,
    recipient: str,
    subject: str,
    text_body: str,
) -> None:
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text_body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError from error
