from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import JobSeekerProfile, RecruiterProfile

class JobSeekerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    headline = forms.CharField(max_length=255)
    skills = forms.CharField(widget=forms.Textarea)
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
            JobSeekerProfile.objects.create(
                user=user,
                headline=self.cleaned_data["headline"],
                skills=self.cleaned_data["skills"],
                education=self.cleaned_data["education"],
                work_experience=self.cleaned_data["work_experience"],
                links=self.cleaned_data["links"],
            )
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