from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.http import HttpResponse

from twilio.base.exceptions import TwilioRestException

from accounts.models import JobSeekerProfile, RecruiterProfile
from .forms import EmailContactForm
from .models import Connection
from .services import get_or_create_conversation, ensure_participant

# Import your services
from . import services as dm
from .services import (
    send_contact_email,
    create_twilio_access_token,
    get_or_create_conversation,
    ensure_participant,
    can_message,
    get_twilio_client,
    request_connection,
    respond_connection,
    remove_connection,
    _unique_name_for_pair,
)

User = get_user_model()
RATE_LIMIT_SECONDS = getattr(settings, "CONTACT_RATE_LIMIT_SECONDS", 60)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"

def _can_message(viewer, target) -> bool:
    try:
        return can_message(viewer, target)
    except Exception:
        # Fallback: block self, allow others
        return viewer.id != target.id

def redirect_back(request, fallback_name="accounts:profile", **fallback_kwargs):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt:
        return redirect(nxt)
    return redirect(
        reverse(fallback_name, kwargs=fallback_kwargs) if fallback_kwargs else reverse(fallback_name)
    )

def _get_profile_for_user_id(user_id: int):
    js = JobSeekerProfile.objects.select_related("user").filter(user_id=user_id).first()
    if js:
        return js
    return get_object_or_404(
        RecruiterProfile.objects.select_related("user"),
        user_id=user_id
    )

# -------------------------------------------------------------------
# Email Contact
# -------------------------------------------------------------------
@login_required
@require_POST
def contact_user(request, user_id: int):
    # Resolve target
    profile = _get_profile_for_user_id(user_id)
    target = profile.user

    # Basic guards
    if target.id == request.user.id or not target.email:
        messages.error(request, "This user cannot be contacted.")
        return redirect("accounts:view_profile", user_id=user_id)

    # Privacy rules (jobseeker only)
    if isinstance(profile, JobSeekerProfile):
        privacy = (profile.privacy or "").lower()
        if privacy == "private":
            messages.error(request, "This user is not accepting messages.")
            return redirect("accounts:view_profile", user_id=user_id)
        if privacy in {"employers_only", "employers"} and not hasattr(request.user, "recruiterprofile"):
            messages.error(request, "Only employers can contact this job seeker.")
            return redirect("accounts:view_profile", user_id=user_id)

    # Rate-limit per (sender, recipient)
    rl_key = f"contact:{request.user.id}:{target.id}"
    if cache.get(rl_key):
        messages.error(request, "Please wait a minute before sending another email.")
        return redirect("accounts:view_profile", user_id=user_id)

    subject = (request.POST.get("subject") or "").strip()
    message = (request.POST.get("message") or "").strip()
    if not subject or not message:
        messages.error(request, "Subject and message are required.")
        return redirect("accounts:view_profile", user_id=user_id)

    # Send via Resend
    try:
        send_contact_email(
            request=request,
            to_email=target.email,
            subject=subject,
            message=message,
            reply_to=(request.user.email or None),
        )
        cache.set(rl_key, True, timeout=RATE_LIMIT_SECONDS)
        messages.success(request, f"Email sent to {target.username}.")
    except Exception as e:
        messages.error(request, f"Failed to send email: {e}")

    # Always go back to the same profile
    return redirect("accounts:view_profile", user_id=user_id)

# -------------------------------------------------------------------
# Direct Messaging (Twilio) – JSON endpoints used by base.html
# -------------------------------------------------------------------
@login_required
@require_GET
def get_twilio_token(request):
    token = create_twilio_access_token(request.user)
    if isinstance(token, (bytes, bytearray)):
        token = token.decode("utf-8")
    
    identity = f"user_{request.user.id}"
    
    return JsonResponse({
        "token": token,
        "identity": identity
    })

@login_required
def start_conversation(request, user_id: int):
    other = get_object_or_404(User, id=user_id)

    # Prevent self-messaging
    if other.id == request.user.id:
        return JsonResponse({"error": "Cannot message yourself."}, status=400)

    # Check if user has permission to message this person
    if not _can_message(request.user, other):
        return JsonResponse({
            "error": "You don't have permission to message this user."
        }, status=403)

    try:
        # Get or create the conversation (stores both usernames in attributes)
        conv_sid = get_or_create_conversation(request.user.id, other.id)
        
        # Ensure both participants are added
        ensure_participant(conv_sid, request.user.id)
        ensure_participant(conv_sid, other.id)
        
        # Return just the other person's username as friendly_name
        return JsonResponse({
            "ok": True,
            "sid": conv_sid,
            "other_id": other.id,
            "other_username": other.username,
            "friendly_name": other.username
        })
        
    except TwilioRestException as e:
        error_msg = str(e)
        print(f"[start_conversation] Twilio API Error: {error_msg}")
        return JsonResponse({
            "ok": False,
            "error": f"Twilio API Error: {error_msg}"
        }, status=500)
        
    except Exception as e:
        error_msg = str(e)
        print(f"[start_conversation] Unexpected Error: {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "ok": False,
            "error": error_msg
        }, status=500)

@login_required
@require_GET
def list_conversations(request):
    client = get_twilio_client()
    identity = f"user_{request.user.id}"

    data = []

    try:
        # Use Twilio Users API - this automatically filters to only conversations
        # where the current user is a participant
        print(f"[list_conversations] Fetching conversations for {identity}")
        items = client.conversations.v1.users(identity).user_conversations.list(limit=100)
        
        print(f"[list_conversations] Found {len(items)} user conversations")
        
        for uc in items:
            try:
                conv = client.conversations.v1.services(dm.CONV_SERVICE_SID)\
                    .conversations(uc.conversation_sid).fetch()
                    
                friendly_name = getattr(conv, "friendly_name", None) or uc.conversation_sid
                
                data.append({
                    "sid": uc.conversation_sid,
                    "friendly_name": friendly_name,
                })
            except Exception as e:
                print(f"[list_conversations] Error fetching conversation {uc.conversation_sid}: {e}")
                # Include the conversation even if we can't fetch details
                data.append({
                    "sid": uc.conversation_sid,
                    "friendly_name": uc.conversation_sid,
                })
        
        print(f"[list_conversations] Returning {len(data)} conversations")
        return JsonResponse({"conversations": data})
        
    except TwilioRestException as e:
        # If user doesn't exist in Twilio yet, return empty list
        print(f"[list_conversations] Twilio error for {identity}: {e}")
        return JsonResponse({"conversations": []})
    except Exception as e:
        # For any other error, log and return empty list (don't expose all conversations)
        print(f"[list_conversations] Error listing conversations: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"conversations": []})

@login_required
@require_GET
def conversation_view(request, conversation_sid: str):
    client = get_twilio_client()
    identity = f"user_{request.user.id}"
    
    try:
        # Fetch the conversation
        conv = client.conversations.v1.services(dm.CONV_SERVICE_SID)\
            .conversations(conversation_sid).fetch()
        
        # Verify user is a participant
        participants = conv.participants.list()
        participant_identities = [p.identity for p in participants]
        
        print(f"[conversation_view] Conv {conversation_sid} has participants: {participant_identities}")
        
        if identity not in participant_identities:
            print(f"[conversation_view] User {identity} not in participants, denying access")
            return JsonResponse({"error": "Unauthorized"}, status=403)
        
        friendly_name = getattr(conv, "friendly_name", None) or conv.sid
        
        return JsonResponse({
            "sid": conv.sid,
            "friendly_name": friendly_name,
        })
    except TwilioRestException as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception as e:
        print(f"[conversation_view] Error: {e}")
        return JsonResponse({"error": "Internal error"}, status=500)

# -------------------------------------------------------------------
# Connections
# -------------------------------------------------------------------
@login_required
@require_POST
def connections_request(request, user_id):
    other = get_object_or_404(User, id=user_id)
    try:
        request_connection(request.user, other)
        messages.success(request, f"Connection request sent to {other.username}.")
    except Exception as e:
        messages.error(request, f"Could not send request: {e}")
    return redirect_back(request)

@login_required
@require_POST
def connections_accept(request, user_id):
    try:
        respond_connection(request.user, requester_id=user_id, accept=True)
        messages.success(request, "Connection accepted.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect_back(request)

@login_required
@require_POST
def connections_decline(request, user_id):
    try:
        respond_connection(request.user, requester_id=user_id, accept=False)
        messages.info(request, "Connection declined.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect_back(request)

@login_required
@require_POST
def connections_remove(request, user_id):
    try:
        remove_connection(request.user.id, user_id)
        messages.info(request, "Connection removed.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect_back(request)

@login_required
@require_GET
def api_connections(request):
    qs = Connection.objects.filter(status=Connection.Status.ACCEPTED).filter(
        models.Q(requester=request.user) | models.Q(addressee=request.user)
    )
    other_ids = [
        c.addressee_id if c.requester_id == request.user.id else c.requester_id
        for c in qs
    ]
    users = User.objects.filter(id__in=other_ids).values("id", "username")
    return JsonResponse(list(users), safe=False)