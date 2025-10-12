# jobs/forms.py
from django import forms
from .models import Job, Skill

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'visa_sponsorship', 'location',
            'pay_min', 'pay_max', 'pay_type', 'description',
            'image', 'required_skills', 'preferred_skills'
        ]
        widgets = {
            'required_skills': forms.CheckboxSelectMultiple,
            'preferred_skills': forms.CheckboxSelectMultiple,
        }
