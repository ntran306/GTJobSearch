from django.db import models
from django.contrib.auth.models import User

class JobSeekerProfile(models.Model):
    # Privacy choices for profile visibility
    PRIVACY_CHOICES = [
        ('public', 'Visible to All Employers and Job Seekers'),
        ('employers_only', 'Visible to Employers Only'),
        ('private', 'Visible to Me Only'),
    ]


    user = models.OneToOneField(User, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255, blank=True)
    skills = models.ManyToManyField('jobs.Skill', blank=True, related_name='jobseekers')
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.URLField(blank=True, null=True)  # <-- make optional
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')

    def __str__(self):
        return f"{self.user.username}'s Profile"

class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, default="Sole Proprietorship")
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.name} (Recruiter)"
