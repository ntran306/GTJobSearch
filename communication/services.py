import resend
from django.conf import settings
from django.utils.html import escape
from .models import Connection
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
import os

# Twilio
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from twilio.base.exceptions import TwilioRestException

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID")
API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET")
CONV_SERVICE_SID = os.environ.get("TWILIO_CONVERSATIONS_SERVICE_SID")

User = get_user_model()

# ----- Email (RESEND API) ----- #
resend.api_key = settings.RESEND_API_KEY

def render_safe_html(text: str) -> str:
    return f"<p>{escape(text).replace(chr(10), '<br/>')}</p>"

def send_contact_email(*args, **kwargs):
    """
    Compatible call signatures:
      send_contact_email(request, to_email, subject, message, html=None, reply_to=None)
      send_contact_email(to_email, subject, message, html=None, reply_to=None)

    Always displays sender's username and real email.
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

# ----- Direct Messaging (Twilio Conversations) ----- #

def get_twilio_client():
    if not all([ACCOUNT_SID, AUTH_TOKEN]):
        raise RuntimeError("Twilio ACCOUNT_SID/AUTH_TOKEN missing")
    return Client(ACCOUNT_SID, AUTH_TOKEN)

def _unique_name_for_pair(a_id: int, b_id: int) -> str:
    """Generate unique conversation name for a pair of users"""
    lo, hi = sorted([int(a_id), int(b_id)])
    return f"userpair_{lo}_{hi}"

def _get_usernames_for_conversation(a_id: int, b_id: int) -> tuple:
    """Get usernames for both users in a conversation"""
    try:
        user_a = User.objects.get(id=a_id)
        user_b = User.objects.get(id=b_id)
        return user_a.username, user_b.username
    except User.DoesNotExist:
        return f"User{a_id}", f"User{b_id}"

def _find_conversation_by_unique_name(client, unique_name: str):
    for conv in client.conversations.v1.conversations.list(limit=200):
        if getattr(conv, "unique_name", None) == unique_name:
            return conv
    return None

def create_twilio_access_token(django_user) -> str:
    if not all([ACCOUNT_SID, API_KEY_SID, API_KEY_SECRET, CONV_SERVICE_SID]):
        raise RuntimeError("Twilio API key or service SID missing")

    # FIXED: Use format "user_{id}" instead of "user:{id}"
    identity = f"user_{django_user.id}"
    
    print(f"[create_token] Creating token for {identity} with service {CONV_SERVICE_SID}")

    token = AccessToken(ACCOUNT_SID, API_KEY_SID, API_KEY_SECRET, identity=identity)
    token.ttl = 3600  # 1 hour
    
    grant = ChatGrant(service_sid=CONV_SERVICE_SID)
    token.add_grant(grant)

    jwt = token.to_jwt()
    return jwt.decode("utf-8") if isinstance(jwt, (bytes, bytearray)) else jwt

def get_or_create_conversation(a_id: int, b_id: int, requesting_user_id: int = None) -> str:
    """
    Get or create a conversation between two users.
    Returns the conversation SID.
    """
    import json
    
    client = get_twilio_client()
    unique = _unique_name_for_pair(a_id, b_id)
    
    # Get usernames for both users
    try:
        user_a = User.objects.get(id=a_id)
        user_b = User.objects.get(id=b_id)
        username_a = user_a.username
        username_b = user_b.username
    except User.DoesNotExist as e:
        print(f"[get_or_create_conversation] ERROR: User not found - {e}")
        username_a = f"User{a_id}"
        username_b = f"User{b_id}"
    
    # Create attributes mapping user IDs to usernames
    attributes = {
        f"user_{a_id}": username_a,
        f"user_{b_id}": username_b
    }
    attributes_json = json.dumps(attributes)
    
    print(f"[get_or_create_conversation] Looking for: {unique}")
    print(f"[get_or_create_conversation] Users: {username_a} (ID: {a_id}) and {username_b} (ID: {b_id})")
    print(f"[get_or_create_conversation] Attributes JSON: {attributes_json}")
    print(f"[get_or_create_conversation] Service SID: {CONV_SERVICE_SID}")
    
    # Scan service conversations first
    try:
        svc = client.conversations.v1.services(CONV_SERVICE_SID)
        for conv in svc.conversations.list(limit=1000):
            if getattr(conv, "unique_name", None) == unique:
                print(f"[get_or_create_conversation] Found existing: {conv.sid}")
                
                # Always update attributes to ensure they're current
                try:
                    updated = client.conversations.v1.services(CONV_SERVICE_SID)\
                        .conversations(conv.sid)\
                        .update(attributes=attributes_json)
                    print(f"[get_or_create_conversation] ✓ Updated attributes successfully")
                    print(f"[get_or_create_conversation] Stored attributes: {updated.attributes}")
                except Exception as e:
                    print(f"[get_or_create_conversation] ✗ Failed to update attributes: {e}")
                
                return conv.sid
    except Exception as e:
        print(f"[get_or_create_conversation] Error scanning service: {e}")
    
    # Create new conversation with attributes
    try:
        print(f"[get_or_create_conversation] Creating new conversation: {unique}")
        
        svc = client.conversations.v1.services(CONV_SERVICE_SID)
        conv = svc.conversations.create(
            unique_name=unique,
            attributes=attributes_json
        )
        print(f"[get_or_create_conversation] ✓ Created: {conv.sid}")
        print(f"[get_or_create_conversation] ✓ Attributes set: {conv.attributes}")
        return conv.sid
    except TwilioRestException as e:
        if getattr(e, "status", None) == 409:
            # Race condition - try to find it again
            print(f"[get_or_create_conversation] Got 409 conflict, scanning again...")
            svc = client.conversations.v1.services(CONV_SERVICE_SID)
            for conv in svc.conversations.list(limit=1000):
                if getattr(conv, "unique_name", None) == unique:
                    print(f"[get_or_create_conversation] Found after 409: {conv.sid}")
                    
                    # Update attributes on found conversation
                    try:
                        client.conversations.v1.services(CONV_SERVICE_SID)\
                            .conversations(conv.sid)\
                            .update(attributes=attributes_json)
                        print(f"[get_or_create_conversation] ✓ Updated attributes after 409")
                    except Exception as update_err:
                        print(f"[get_or_create_conversation] ✗ Could not update attributes: {update_err}")
                    
                    return conv.sid
        print(f"[get_or_create_conversation] ✗ FAILED to create conversation: {e}")
        raise

def ensure_participant(conversation_sid: str, user_id: int):
    """
    Ensure a user is a participant in a conversation.
    Uses format "user_{id}" for identity.
    """
    # FIXED: Use format "user_{id}" instead of "user:{id}"
    identity = f"user_{user_id}"
    client = get_twilio_client()
    
    print(f"[ensure_participant] Adding {identity} to {conversation_sid}")
    
    try:
        svc = client.conversations.v1.services(CONV_SERVICE_SID)
        svc.conversations(conversation_sid).participants.create(identity=identity)
        print(f"[ensure_participant] Added {identity}")
    except TwilioRestException as e:
        error_msg = str(e).lower()
        # Ignore "already exists" errors
        if getattr(e, "status", None) == 409 or "already" in error_msg or "exists" in error_msg:
            print(f"[ensure_participant] {identity} already in conversation")
            return
        print(f"[ensure_participant] Error adding {identity}: {e}")
        raise

def can_message(viewer_user, target_user) -> bool:
    from accounts.models import JobSeekerProfile, RecruiterProfile

    # same user? block
    if viewer_user.id == target_user.id:
        return False

    js = JobSeekerProfile.objects.filter(user=target_user).first()
    if js:
        p = (js.privacy or "").strip().lower()
        if p == "private":
            return False
        if p in {"employers_only", "employers"}:
            is_recruiter = RecruiterProfile.objects.filter(user=viewer_user).exists()
            return is_recruiter or is_connected(viewer_user.id, target_user.id)
        # public → require accepted connection
        return is_connected(viewer_user.id, target_user.id)

    # Target is recruiter or neither profile → require accepted connection
    return is_connected(viewer_user.id, target_user.id)

# --- Connections Between Users --- #

def connection_status(a_id: int, b_id: int) -> str | None:
    """
    Get the connection status string for a pair of users, or None if none exists.
    """
    c = (Connection.objects
         .filter(requester_id=a_id, addressee_id=b_id)
         .union(Connection.objects.filter(requester_id=b_id, addressee_id=a_id))
         .first())
    return c.status if c else None

def is_connected(a_id: int, b_id: int) -> bool:
    return connection_status(a_id, b_id) == Connection.Status.ACCEPTED

def request_connection(requester, addressee) -> Connection:
    if requester.id == addressee.id:
        raise ValueError("Cannot connect to yourself.")
    c, created = Connection.objects.get_or_create(
        requester=requester, addressee=addressee,
        defaults={"status": Connection.Status.PENDING}
    )
    if not created and c.status == Connection.Status.DECLINED:
        c.status = Connection.Status.PENDING
        c.created_at = timezone.now()
        c.responded_at = None
        c.save(update_fields=["status","created_at","responded_at"])
    return c

def respond_connection(addressee, requester_id: int, accept: bool) -> Connection:
    c = Connection.objects.get(requester_id=requester_id, addressee=addressee)
    c.status = Connection.Status.ACCEPTED if accept else Connection.Status.DECLINED
    c.responded_at = timezone.now()
    c.save(update_fields=["status","responded_at"])
    return c

def remove_connection(a_id: int, b_id: int) -> int:
    return Connection.objects.filter(
        (models.Q(requester_id=a_id, addressee_id=b_id) |
         models.Q(requester_id=b_id, addressee_id=a_id)),
        status=Connection.Status.ACCEPTED
    ).delete()[0]