# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

class AddressFields(models.Model):
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    state_region = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    postal_code = models.CharField(max_length=32,  blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True, db_index=True)

    # Optional lat/lng for geo search (Decimal; nullable so existing rows are fine)
    latitude      = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, db_index=True)
    longitude     = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["city", "state_region"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    @property
    def has_geo(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def full_address(self) -> str:
        parts = [
            self.address_line1 or "",
            self.address_line2 or "",
            ", ".join([p for p in [self.city, self.state_region] if p]),
            self.postal_code or "",
            self.country or "",
        ]
        return ", ".join([p.strip() for p in parts if p and p.strip()])


class JobSeekerProfile(AddressFields):
    PRIVACY_CHOICES = [
        ('public', 'Visible to All Employers and Job Seekers'),
        ('employers_only', 'Visible to Employers Only'),
        ('private', 'Visible to Me Only'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='jobseekerprofile', blank=True, null=True)
    headline = models.CharField(max_length=255, blank=True)
    skills = models.ManyToManyField('jobs.Skill', blank=True, related_name='jobseekers')
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.URLField(blank=True, null=True)
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')

    location = models.CharField(max_length=255, blank=True, null=True)

    projects = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Job Seeker Profile"


class RecruiterProfile(AddressFields):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiterprofile', blank=True, null=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, default="Sole Proprietorship")
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Optional display field, mirroring JobSeeker’s "location"
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} (Recruiter)"

@receiver(pre_delete, sender=RecruiterProfile)
def delete_recruiter_jobs(sender, instance, **kwargs):
    """Delete all jobs owned by this recruiter before the profile is deleted"""
    try:
        from jobs.models import Job
        jobs = Job.objects.filter(recruiter=instance)
        job_count = jobs.count()
        jobs.delete()
        print(f"Deleted {job_count} jobs for recruiter: {instance.name}")
    except Exception as e:
        print(f"Warning: couldn't auto-delete jobs for recruiter: {e}")


@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Clean up all user data before deletion.
    This ensures that even if some relations don't cascade properly,
    we explicitly clean them up.
    """
    print(f"Cleaning up data for user: {instance.username}")
    
    # If user is a recruiter, delete their jobs BEFORE the profile is deleted
    try:
        if hasattr(instance, 'recruiterprofile'):
            from jobs.models import Job
            recruiter_profile = instance.recruiterprofile
            jobs = Job.objects.filter(recruiter=recruiter_profile)
            job_count = jobs.count()
            jobs.delete()
            print(f"  - Deleted {job_count} jobs for recruiter")
    except Exception as e:
        print(f"  - Error deleting jobs: {e}")
    
    # Delete all applications (should cascade via CASCADE, but being explicit)
    try:
        from applications.models import Application
        app_count = instance.applications.count()
        instance.applications.all().delete()
        print(f"  - Deleted {app_count} applications")
    except Exception as e:
        print(f"  - Error deleting applications: {e}")
    
    # Delete all connections (both as requester and addressee)
    try:
        from communication.models import Connection
        conn_out_count = instance.connections_out.count()
        conn_in_count = instance.connections_in.count()
        instance.connections_out.all().delete()
        instance.connections_in.all().delete()
        print(f"  - Deleted {conn_out_count + conn_in_count} connections")
    except Exception as e:
        print(f"  - Error deleting connections: {e}")
    
    print(f"User cleanup complete for: {instance.username}")