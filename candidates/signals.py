# candidates/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from accounts.models import JobSeekerProfile
from .models import Candidate

