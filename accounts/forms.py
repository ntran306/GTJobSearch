from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobSeekerProfile, RecruiterProfile

class JobSeekerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    headline = forms.CharField(max_length=255)
    skills = forms.ModelMultipleChoiceField(
        queryset=None,  # temporarily None
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the skills you have"
    )
    education = forms.CharField(widget=forms.Textarea)
    work_experience = forms.CharField(widget=forms.Textarea)
    links = forms.URLField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2",
                  "headline", "skills", "education", "work_experience", "links")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jobs.models import Skill
        self.fields['skills'].queryset = Skill.objects.all()

class RecruiterSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=255)
    company = forms.CharField(max_length=255)
    website = forms.URLField(required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "name", "company", "website", "description")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            RecruiterProfile.objects.create(
                user=user,
                name=self.cleaned_data["name"],
                company=self.cleaned_data["company"],
                website=self.cleaned_data.get("website", ""),
                description=self.cleaned_data.get("description", "")
            )
        return user


class JobSeekerProfileForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=None,  # temporarily None
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the skills you have"
    )

    class Meta:
        model = JobSeekerProfile
        fields = ['headline', 'skills', 'education', 'work_experience', 'links']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jobs.models import Skill
        self.fields['skills'].queryset = Skill.objects.all()

        # Add form-input classes and textarea attributes
        for name, field in self.fields.items():
            if name == 'skills':
                continue
            existing = field.widget.attrs.get('class', "")
            field.widget.attrs['class'] = (existing + " form-input").strip()
            if isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs.setdefault('rows', 5)
                field.widget.attrs.setdefault('style', 'min-height:100px;')
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label if field.label else ""


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ['name', 'company', 'website', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', "")
            field.widget.attrs['class'] = (existing + " form-input").strip()
            if isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs.setdefault('rows', 5)
                field.widget.attrs.setdefault('style', 'min-height:100px;')
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label if field.label else ""
