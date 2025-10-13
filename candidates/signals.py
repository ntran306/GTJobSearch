# candidates/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from accounts.models import JobSeekerProfile
from .models import Candidate

@receiver(post_save, sender=JobSeekerProfile)
def sync_candidate_profile(sender, instance, created, **kwargs):
    """
    Safely create or sync a Candidate object when a JobSeekerProfile is created or updated.
    Uses transaction.on_commit() to ensure DB consistency and avoids FK errors.
    """
    def _sync():
        try:
            candidate, _ = Candidate.objects.get_or_create(
                user=instance.user,
                defaults={'location': instance.location or '', 'bio': instance.headline or ''}
            )

            # ✅ Only sync if instance.skills exists and has valid Skill IDs
            if hasattr(instance, 'skills') and instance.skills.exists():
                valid_skill_ids = [
                    skill.id for skill in instance.skills.all()
                    if skill.id is not None
                ]
                candidate.skills.set(valid_skill_ids)

            # ✅ Optional sync: bio/location
            candidate.location = instance.location or candidate.location
            candidate.bio = instance.headline or candidate.bio

            candidate.save()

        except Exception as e:
            print(f"[Signal Error] Failed to sync Candidate for {instance.user.username}: {e}")

    # ✅ Run only after full DB commit
    transaction.on_commit(_sync)
