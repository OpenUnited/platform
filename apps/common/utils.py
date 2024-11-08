import os
import uuid

from django.conf import settings
from django.forms import ModelForm

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_sendgrid_email(to_emails, subject, content):
    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to_emails,
            subject=subject,
            html_content=content,
        )

        if not settings.DEBUG:
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            sg.send(message)
        else:
            print("Email sent:", flush=True)
            print(message, flush=True)
    except Exception as e:
        print("Send Grid Email Failed:", e, flush=True)


class BaseModelForm(ModelForm):
    """
    Base model form with common functionality for all model forms
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

def serialize_tree(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "node_id": uuid.uuid4(),
        "name": node.name,
        "description": node.description,
        "video_link": node.video_link,
        "video_name": node.video_name,
        "video_duration": node.video_duration,
        "has_saved": True,
        "children": [serialize_tree(child) for child in node.get_children()],
    }

