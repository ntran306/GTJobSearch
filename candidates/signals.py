from django.db.models.signals import post_save
from django.dispatch import receiver
from profiles.models import Profile
from .models import SavedFilter, FilterNotification

@receiver(post_save, sender=Profile)
def check_saved_filters_on_profile_update(sender, instance, created, **kwargs):
    """
    When a profile is created or updated, check all saved filters
    with notifications enabled
    """
    # Skip if this is a recruiter profile
    if instance.is_recruiter:
        return
    
    # Only check for newly created profiles OR significant updates
    # You can modify this to check on every update if you want
    if not created:
        return
    
    # Get all saved filters with notifications enabled
    active_filters = SavedFilter.objects.filter(notify_on_match=True)
    
    for saved_filter in active_filters:
        # Check if this profile matches the filter
        if saved_filter.matches_profile(instance):
            # Check if notification already exists (avoid duplicates)
            existing_notification = FilterNotification.objects.filter(
                recruiter=saved_filter.recruiter,
                candidate=instance.user,
                saved_filter=saved_filter
            ).exists()
            
            if not existing_notification:
                # Create notification
                filter_description = []
                if saved_filter.skill:
                    filter_description.append(f"skill: {saved_filter.skill}")
                if saved_filter.location:
                    filter_description.append(f"location: {saved_filter.location}")
                if saved_filter.project:
                    filter_description.append(f"project: {saved_filter.project}")
                
                filter_desc_str = ", ".join(filter_description) if filter_description else "your filter"
                
                FilterNotification.objects.create(
                    recruiter=saved_filter.recruiter,
                    saved_filter=saved_filter,
                    candidate=instance.user,
                    message=f"New candidate {instance.user.username} matches {filter_desc_str}"
                )