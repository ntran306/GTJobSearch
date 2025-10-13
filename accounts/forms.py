from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobSeekerProfile, RecruiterProfile


# ----------------------------
#  JOB SEEKER SIGNUP FORM
# ----------------------------
class JobSeekerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    headline = forms.CharField(max_length=255, required=True)
    skills = forms.ModelMultipleChoiceField(
        queryset=None,  # will be set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the skills you have"
    )
    education = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    work_experience = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    links = forms.URLField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "headline",
            "skills",
            "education",
            "work_experience",
            "links",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dynamically load skills from jobs.models.Skill
        from jobs.models import Skill
        self.fields["skills"].queryset = Skill.objects.all()

    def save(self, commit=True):
        """
        Creates a User and links a JobSeekerProfile with all the extra fields.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

            # Create associated JobSeekerProfile
            profile = JobSeekerProfile.objects.create(
                user=user,
                headline=self.cleaned_data.get("headline"),
                education=self.cleaned_data.get("education"),
                work_experience=self.cleaned_data.get("work_experience"),
                links=self.cleaned_data.get("links"),
            )

            # Save ManyToMany skills relationship
            skills = self.cleaned_data.get("skills")
            if skills:
                profile.skills.set(skills)

            profile.save()

        return user


# ----------------------------
#  RECRUITER SIGNUP FORM
# ----------------------------
class RecruiterSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=255, required=True)
    company = forms.CharField(max_length=255, required=True)
    website = forms.URLField(required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "name",
            "company",
            "website",
            "description",
        )

    def save(self, commit=True):
        """
        Creates a User and linked RecruiterProfile.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            RecruiterProfile.objects.create(
                user=user,
                name=self.cleaned_data["name"],
                company=self.cleaned_data["company"],
                website=self.cleaned_data.get("website", ""),
                description=self.cleaned_data.get("description", ""),
            )

        return user


# ----------------------------
#  JOB SEEKER PROFILE FORM (for editing)
# ----------------------------
class JobSeekerProfileForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=None,  # set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the skills you have"
    )

    class Meta:
        model = JobSeekerProfile
        fields = ["headline", "skills", "education", "work_experience", "links"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jobs.models import Skill
        self.fields["skills"].queryset = Skill.objects.all()

        # Add nicer styles
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-input").strip()
            if isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs.setdefault("rows", 5)
                field.widget.attrs.setdefault("style", "min-height:100px;")
            if not field.widget.attrs.get("placeholder"):
                field.widget.attrs["placeholder"] = field.label or ""


# ----------------------------
#  RECRUITER PROFILE FORM (for editing)
# ----------------------------
class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ["name", "company", "website", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-input").strip()
            if isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs.setdefault("rows", 5)
                field.widget.attrs.setdefault("style", "min-height:100px;")
            if not field.widget.attrs.get("placeholder"):
                field.widget.attrs["placeholder"] = field.label or ""
