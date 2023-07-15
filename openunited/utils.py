import os
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_sendgrid_email(to_emails, subject, content):
    try:
        message = Mail(
            from_email=settings.EMAIL_HOST,
            to_emails=to_emails,
            subject=subject,
            html_content=content
        )

        if not settings.DEBUG:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg.send(message)
        else:
            print("Email sent:", flush=True)
            print(message, flush=True)
    except Exception as e:
        print("Send Grid Email Failed:", e, flush=True)
