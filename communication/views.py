from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.models import JobSeekerProfile, RecruiterProfile
from .services import send_contact_email
from .forms import EmailContactForm
from django.conf import settings

RATE_LIMIT_SECONDS = getattr(settings, "CONTACT_RATE_LIMIT_SECONDS", 60)

def _get_profile_for_user_id(user_id: int):
    js = JobSeekerProfile.objects.select_related("user").filter(user_id=user_id).first()
    if js:
        return js
    return get_object_or_404(RecruiterProfile.objects.select_related("user"), user_id=user_id)

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