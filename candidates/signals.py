from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import JobSeekerProfile
from .models import Candidate

@receiver(post_save, sender=JobSeekerProfile)
def create_candidate_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Candidate object whenever a JobSeekerProfile is created.
    """
    if created:
        Candidate.objects.create(user=instance.user, location='', bio='')
    else:
        # Update existing candidate profile if JobSeekerProfile changes
        candidate, _ = Candidate.objects.get_or_create(user=instance.user)
        # You can sync some fields if you want:
        # candidate.bio = instance.headline or candidate.bio
        candidate.skills.set(instance.skills.all())
        candidate.save()

