import resend
from django.conf import settings
from django.utils.html import escape

# ----- Email (RESEND API) ----- #
resend.api_key = settings.RESEND_API_KEY

def render_safe_html(text: str) -> str:
    return f"<p>{escape(text).replace(chr(10), '<br/>')}</p>"

def send_contact_email(*args, **kwargs):
    """
    Compatible call signatures:
      send_contact_email(request, to_email, subject, message, html=None, reply_to=None)
      send_contact_email(to_email, subject, message, html=None, reply_to=None)

    Always displays sender’s username and real email.
    """

    # ---- normalize arguments ----
    request = kwargs.pop("request", None)
    html = kwargs.pop("html", None)
    reply_to = kwargs.pop("reply_to", None)

    # unpack positional args safely
    args = list(args)
    if args and hasattr(args[0], "user"):  # detect request object
        request = args.pop(0)

    # extract remaining required fields
    try:
        to_email = args.pop(0) if args else kwargs.pop("to_email")
        subject = args.pop(0) if args else kwargs.pop("subject")
        message = args.pop(0) if args else kwargs.pop("message")
    except KeyError as e:
        raise TypeError(f"send_contact_email() missing required argument: {e.args[0]}")

    # ---- determine sender ----
    user_name = "BuzzedIn User"
    user_email = "no-reply@buzzedinjobs.org"

    if request and hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
        user = request.user
        user_name = getattr(user, "username", user_name)
        if getattr(user, "email", None):
            user_email = user.email

    # visible From line
    if user_email.endswith("@buzzedinjobs.org"):
        from_display = f"{user_name} <{user_email}>"
        reply_to_address = reply_to or user_email
    else:
        from_display = f"{user_name} via BuzzedIn <no-reply@buzzedinjobs.org>"
        reply_to_address = reply_to or user_email

    # ---- build HTML body ----
    html_body = html or f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p style="margin: 0; padding: 8px 0; font-weight: bold;">
                Sent by: {user_name} ({user_email})
            </p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 8px 0;">
            {render_safe_html(message)}
        </div>
    """

    payload = {
        "from": from_display,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": f"Sent by {user_name} ({user_email})\n\n{message}",
        "reply_to": reply_to_address,
    }

    try:
        return resend.Emails.send(payload)
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise

# ----- Direct Messaging ----- #