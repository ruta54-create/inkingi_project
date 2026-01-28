from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP/email configuration'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        recipient = options['recipient']
        subject = f"[{settings.DEFAULT_FROM_EMAIL}] Test email from Inkingi Woods"
        message = 'This is a test email sent from the Inkingi Woods application to verify SMTP settings.'
        from_email = settings.DEFAULT_FROM_EMAIL
        try:
            send_mail(subject, message, from_email, [recipient])
            self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to {recipient}'))
        except Exception as e:
            raise CommandError(f'Failed to send test email: {e}')
