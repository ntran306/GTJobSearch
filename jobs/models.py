from django.db import models
from django.conf import settings

# Will try to make it nicer and more flexible in terms of salary filtering
PAY_TYPE_CHOICES = [
    ('annual', 'Annual'),
    ('hourly', 'Hourly'),
    ('monthly', 'Monthly'),
]

class Job(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default='Remote')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)   # Leave lat and long in for Google Maps API in future
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pay_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_max = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='annual')
    description = models.TextField()
    image = models.ImageField(upload_to='job_images/')

    def __str__(self):
        return str(self.id) + " - " + self.name + " | " + self.company
