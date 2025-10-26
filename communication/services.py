import resend
from django.conf import settings
from django.utils.html import escape
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# ----- Email (Resend) ----- #
def render_safe_html(text: str) -> str:
    return f"<p>{escape(text).replace(chr(10), '<br/>')}</p>"

def send_contact_email(*, to_email: str, subject: str, message: str, reply_to: str | None = None):
    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set") # Check to makesure API key works

    resend.api_key = settings.RESEND_API_KEY

    html_body = render_safe_html(message)
    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    if reply_to:
        payload["reply_to"] = [reply_to]

    return resend.Emails.send(payload)

# ----- Direct Messaging ----- #