# Email configuration

This project supports sending email via SMTP. For local development the project uses the console email backend (prints emails to the runserver console) by default. To have emails delivered to a real inbox, configure environment variables.

## Environment variables

- EMAIL_HOST — SMTP host (e.g. smtp.sendgrid.net, smtp.mailtrap.io)
- EMAIL_PORT — SMTP port (default: 587)
- EMAIL_HOST_USER — SMTP username
- EMAIL_HOST_PASSWORD — SMTP password (or API key)
- EMAIL_USE_TLS — Use TLS (true/false). Default: true
- EMAIL_USE_SSL — Use SSL (true/false). Default: false
- DEFAULT_FROM_EMAIL — From address for outgoing mail (e.g. noreply@example.com)

Place these variables in your environment (or .env if you use a loader) before starting the Django process. Example (PowerShell):

$env:EMAIL_HOST = 'smtp.mailtrap.io';
$env:EMAIL_HOST_USER = 'your-mailtrap-user';
$env:EMAIL_HOST_PASSWORD = 'your-mailtrap-pass';
$env:DEFAULT_FROM_EMAIL = 'noreply@example.com';

## Examples

### Mailtrap (testing)
- EMAIL_HOST: smtp.mailtrap.io
- EMAIL_PORT: 587
- EMAIL_HOST_USER: <your mailtrap user>
- EMAIL_HOST_PASSWORD: <your mailtrap password>
- DEFAULT_FROM_EMAIL: noreply@localhost

### SendGrid (production)
- EMAIL_HOST: smtp.sendgrid.net
- EMAIL_PORT: 587
- EMAIL_HOST_USER: apikey
- EMAIL_HOST_PASSWORD: <sendgrid api key>
- EMAIL_USE_TLS: true
- DEFAULT_FROM_EMAIL: noreply@yourdomain.com

## Verify delivery
After configuring and restarting the server, you can:
1. Use the password reset flow and check the target inbox.
2. Or run the management command to send a test email: `python manage.py send_test_email recipient@example.com`.

If you want, I can help configure Mailtrap or SendGrid and verify a test message now.
