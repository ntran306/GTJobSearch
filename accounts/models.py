# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class AddressFields(models.Model):
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    state_region = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    postal_code = models.CharField(max_length=32, blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True, db_index=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["city", "state_region"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    @property
    def has_geo(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def full_address(self):
        parts = [
            self.address_line1 or "",
            self.address_line2 or "",
            ", ".join([p for p in [self.city, self.state_region] if p]),
            self.postal_code or "",
            self.country or "",
        ]
        return ", ".join([p.strip() for p in parts if p.strip()])


class JobSeekerProfile(AddressFields):
    PRIVACY_CHOICES = [
        ('public', 'Visible to All Employers and Job Seekers'),
        ('employers_only', 'Visible to Employers Only'),
        ('private', 'Visible to Me Only'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='jobseekerprofile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
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

    @property
    def resume_filename(self):
        if self.resume:
            return self.resume.name.split('/')[-1]
        return None



class RecruiterProfile(AddressFields):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiterprofile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, default="Sole Proprietorship")
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} (Recruiter)"


@receiver(pre_delete, sender=RecruiterProfile)
def delete_recruiter_jobs(sender, instance, **kwargs):
    try:
        from jobs.models import Job
        count = Job.objects.filter(recruiter=instance).count()
        Job.objects.filter(recruiter=instance).delete()
        print(f"Deleted {count} jobs for recruiter {instance.name}")
    except Exception as e:
        print("Warning: couldn't auto-delete recruiter jobs:", e)


@receiver(pre_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    print(f"Cleaning up data for user: {instance.username}")

    # Jobs
    try:
        if hasattr(instance, "recruiterprofile"):
            from jobs.models import Job
            count = Job.objects.filter(recruiter=instance.recruiterprofile).count()
            Job.objects.filter(recruiter=instance.recruiterprofile).delete()
            print(f"  - Deleted {count} jobs")
    except:
        pass

    # Applications
    try:
        from applications.models import Application
        count = instance.applications.count()
        instance.applications.all().delete()
        print(f"  - Deleted {count} applications")
    except:
        pass

    # Connections
    try:
        from communication.models import Connection
        count = instance.connections_out.count() + instance.connections_in.count()
        instance.connections_out.all().delete()
        instance.connections_in.all().delete()
        print(f"  - Deleted {count} connections")
    except:
        pass

    print(f"Cleanup finished for {instance.username}")
