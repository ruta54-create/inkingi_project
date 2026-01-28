import os
import logging
import smtplib
from email.message import EmailMessage

from django.conf import settings

logger = logging.getLogger(__name__)


def send_smtp_email(to_email, subject, body, html_message=None, from_email=None):
    """Send an email using raw SMTP and env-based config.

    Returns True on success, False on failure.
    """
    host = os.environ.get('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', None))
    port = int(os.environ.get('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', 587) or 587))
    user = os.environ.get('EMAIL_HOST_USER', getattr(settings, 'EMAIL_HOST_USER', None))
    password = os.environ.get('EMAIL_HOST_PASSWORD', getattr(settings, 'EMAIL_HOST_PASSWORD', None))
    use_tls = os.environ.get('EMAIL_USE_TLS', str(getattr(settings, 'EMAIL_USE_TLS', True))).lower() in ('true', '1', 'yes')
    use_ssl = os.environ.get('EMAIL_USE_SSL', str(getattr(settings, 'EMAIL_USE_SSL', False))).lower() in ('true', '1', 'yes')

    if not host:
        logger.error('EMAIL_HOST is not configured; cannot send email')
        return False

    if not from_email:
        from_email = os.environ.get('DEFAULT_FROM_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', user))

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    if isinstance(to_email, (list, tuple)):
        msg['To'] = ', '.join(to_email)
    else:
        msg['To'] = to_email
    msg.set_content(body)
    if html_message:
        msg.add_alternative(html_message, subtype='html')

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        server.ehlo()
        if use_tls and not use_ssl:
            server.starttls()
            server.ehlo()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
        server.quit()
        logger.info('Sent email to %s via %s:%s', to_email, host, port)
        return True
    except Exception as exc:
        logger.exception('Failed to send email to %s: %s', to_email, exc)
        return False
