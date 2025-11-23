import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import SavedFilter, FilterNotification

@login_required
def save_filter(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)
    
    try:
        data = json.loads(request.body.decode())
    except:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)
    
    skill = data.get("skill", "").strip()
    location = data.get("location", "").strip()
    radius = data.get("radius")
    project = data.get("project", "").strip()
    notify_on_match = data.get("notify_on_match", True)  # NEW
    
    if not (skill or location or radius or project):
        return JsonResponse({"ok": False, "error": "Cannot save an empty filter"}, status=400)
    
    saved = SavedFilter.objects.create(
        recruiter=request.user,
        skill=skill,
        location=location,
        radius=radius if radius else None,
        project=project,
        notify_on_match=notify_on_match  # NEW
    )
    
    return JsonResponse({"ok": True, "id": saved.id})


@login_required
def list_filters(request):
    saved = SavedFilter.objects.filter(recruiter=request.user).order_by("-created_at")
    filters = [
        {
            "id": f.id,
            "skill": f.skill,
            "location": f.location,
            "radius": f.radius,
            "project": f.project,
            "notify_on_match": f.notify_on_match,  # NEW
            "created_at": f.created_at.isoformat(),
        }
        for f in saved
    ]
    return JsonResponse({"ok": True, "filters": filters})


@login_required
def delete_filter(request, filter_id):
    try:
        f = SavedFilter.objects.get(id=filter_id, recruiter=request.user)
        f.delete()
        return JsonResponse({"ok": True})
    except SavedFilter.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Not found"}, status=404)


@login_required
def get_notifications(request):
    """Get all notifications for the current recruiter"""
    notifications = FilterNotification.objects.filter(
        recruiter=request.user
    ).select_related('candidate', 'saved_filter')
    
    unread_count = notifications.filter(is_read=False).count()
    
    notifications_data = [
        {
            "id": n.id,
            "message": n.message,
            "candidate_id": n.candidate.id,
            "candidate_username": n.candidate.username,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "filter_id": n.saved_filter.id
        }
        for n in notifications[:20]  # Limit to 20 most recent
    ]
    
    return JsonResponse({
        "ok": True,
        "notifications": notifications_data,
        "unread_count": unread_count
    })


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = FilterNotification.objects.get(
            id=notification_id,
            recruiter=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({"ok": True})
    except FilterNotification.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Not found"}, status=404)


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    FilterNotification.objects.filter(
        recruiter=request.user,
        is_read=False
    ).update(is_read=True)
    return JsonResponse({"ok": True})