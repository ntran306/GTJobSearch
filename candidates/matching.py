from .models import SavedFilter, FilterNotification
from django.contrib.auth.models import User

def check_candidate_against_filters(candidate_profile):
    """
    Call this whenever a candidate updates their profile.
    It will create notifications for recruiters whose filters match.
    """

    recruiter_filters = SavedFilter.objects.filter(notify_on_match=True)
    print("MATCH CHECK RUNNING FOR:", candidate_profile.user.username)  
    for flt in recruiter_filters:
        if flt.matches_profile(candidate_profile):

            # Prevent duplicates (same candidate + same filter)
            already_exists = FilterNotification.objects.filter(
                recruiter=flt.recruiter,
                saved_filter=flt,
                candidate=candidate_profile.user
            ).exists()

            if not already_exists:
                FilterNotification.objects.create(
                    recruiter=flt.recruiter,
                    saved_filter=flt,
                    candidate=candidate_profile.user,
                    message=f"New candidate matches your filter: {candidate_profile.user.username}"
                    

                )
