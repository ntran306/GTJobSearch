# jobs/forms.py
from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
        'title',
        'company',
        'visa_sponsorship',
        'location',
        'pay_min',
        'pay_max',
        'pay_type',
        'description',
        'projects', 
        'image',
        'required_skills',
        'preferred_skills',
    ]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Replace M2M skill fields with CharFields
        # so Django won’t try to auto-save them
        self.fields['required_skills'] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(),
        )
        self.fields['preferred_skills'] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(),
        )

        # ✅ Non-negative pay fields
        self.fields['pay_min'].min_value = 0
        self.fields['pay_max'].min_value = 0

        # ✅ Add placeholders for UX
        self.fields['title'].widget.attrs.update({
            'placeholder': 'e.g., Frontend Developer',
            'class': 'input-field'
        })
        self.fields['company'].widget.attrs.update({
            'placeholder': 'Company Name',
            'class': 'input-field'
        })
        self.fields['location'].widget.attrs.update({
            'placeholder': 'e.g., Remote or Atlanta, GA',
            'class': 'input-field'
        })
        self.fields['description'].widget.attrs.update({
            'placeholder': 'Describe the role, requirements, and culture...',
            'rows': 4,
            'class': 'textarea-field'
        })
        self.fields['projects'] = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List related projects or example work (optional)',
                'class': 'textarea-field'
            })
        )
