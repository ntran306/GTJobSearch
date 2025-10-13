# jobs/forms.py
from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        # Only include fields that the recruiter should fill
        fields = [
            'title', 'company', 'visa_sponsorship', 'location',
            'pay_min', 'pay_max', 'pay_type', 'description',
            'image', 'required_skills', 'preferred_skills'
        ]
        widgets = {
            'required_skills': forms.CheckboxSelectMultiple,
            'preferred_skills': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: make sure pay_min and pay_max are positive
        self.fields['pay_min'].min_value = 0
        self.fields['pay_max'].min_value = 0
