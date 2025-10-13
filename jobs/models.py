from django.db import models
from django.conf import settings
from decimal import Decimal
import requests
from .utils import haversine
from profiles.models import Profile 

PAY_TYPE_CHOICES = [
    ('annual', 'Annual'),
    ('hourly', 'Hourly'),
    ('monthly', 'Monthly'),
]

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobQuerySet(models.QuerySet):
    def filter_within_radius(self, lat, lng, radius):
        job_ids = []
        for job in self:
            if job.latitude and job.longitude:
                distance = haversine(lng, lat, job.longitude, job.latitude)
                if distance <= radius:
                    job_ids.append(job.id)
        return self.filter(id__in=job_ids)

class Job(models.Model):
    id = models.AutoField(primary_key=True)
    
    recruiter = models.ForeignKey(
        "accounts.RecruiterProfile",
        on_delete=models.SET_NULL,   # ✅ allows safe null on delete
        related_name="jobs",
        null=True,                   # ✅ explicitly allows NULL in DB
        blank=True                   # ✅ allows blank in forms
    )
   
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    visa_sponsorship = models.BooleanField(default=False)
    location = models.CharField(max_length=255, default='Remote')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pay_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_max = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='annual')
    description = models.TextField()
    image = models.ImageField(upload_to='job_images/', blank=True, null=True)
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='jobs_requiring')
    preferred_skills = models.ManyToManyField(Skill, blank=True, related_name='jobs_preferring')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = JobQuerySet.as_manager()

    def __str__(self):
        return f"{self.id} - {self.title} | {self.company}"


    def save(self, *args, **kwargs):
        if self.location and (not self.latitude or not self.longitude):
            try:
                api_key = settings.GOOGLE_MAPS_API_KEY_BACKEND
                url = (
                    f"https://maps.googleapis.com/maps/api/geocode/json"
                    f"?address={self.location}&key={api_key}"
                )
                response = requests.get(url)
                data = response.json()
                if data["status"] == "OK":
                    coords = data["results"][0]["geometry"]["location"]
                    self.latitude = Decimal(str(coords["lat"]))
                    self.longitude = Decimal(str(coords["lng"]))
            except Exception as e:
                print(f"Geocoding failed for {self.location}: {e}")
        super().save(*args, **kwargs)
