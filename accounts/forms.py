from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import JobSeekerProfile, RecruiterProfile
from jobs.models import Skill
from .models import JobSeekerProfile


class JobSeekerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    headline = forms.CharField(max_length=255)
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the skills you have (you can select multiple)"
    )
    education = forms.CharField(widget=forms.Textarea)
    work_experience = forms.CharField(widget=forms.Textarea)
    links = forms.URLField(required=False)

    class Meta:
        model = User
        fields = (
            "username", "email", "password1", "password2",
            "headline", "skills", "education", "work_experience", "links"
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = JobSeekerProfile.objects.create(
                user=user,
                headline=self.cleaned_data["headline"],
                education=self.cleaned_data["education"],
                work_experience=self.cleaned_data["work_experience"],
                links=self.cleaned_data["links"],
            )
            # Then set the many-to-many skills relationship
            if self.cleaned_data.get('skills'):
                profile.skills.set(self.cleaned_data['skills'])
        return user

class RecruiterSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            RecruiterProfile.objects.create(
                user=user,
                name=self.cleaned_data["name"],
            )
        return user
    
class JobSeekerProfileForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the skills you have"
    )
    class Meta:
        model = JobSeekerProfile
        fields = ['headline', 'skills', 'education', 'work_experience', 'links']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == 'skills':
                continue
            
            existing = field.widget.attrs.get('class', "")
            classes = (existing + " form-input").strip()
            field.widget.attrs['class'] = classes

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
            classes = (existing + " form-input").strip()
            field.widget.attrs['class'] = classes

            if isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs.setdefault('rows', 5)
                field.widget.attrs.setdefault('style', 'min-height:100px;')

            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label if field.label else ""