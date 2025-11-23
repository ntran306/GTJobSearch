#profiles/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    projects = models.TextField(blank=True)
    company = models.CharField(max_length=255, blank=True)  # for recruiters
    is_recruiter = models.BooleanField(default=False)  # mark recruiters

    def __str__(self):
        return self.user.username

# Signals to auto-create/update Profile whenever a User is created/updated
