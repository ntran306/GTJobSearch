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
    skills = forms.CharField(
        required=True,
        widget=forms.HiddenInput(attrs={'id': 'skillsInput'}),
        help_text="Select your skills"
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
        # Store queryset as an attribute so template can access it
        self.skill_queryset = Skill.objects.all()

    def clean_skills(self):
        """Convert comma-separated skill IDs to a list of Skill objects"""
        from jobs.models import Skill
        
        skills_data = self.cleaned_data.get('skills', '').strip()
        
        # Debug: print what we received
        print(f"DEBUG: Received skills_data: '{skills_data}'")
        
        if not skills_data:
            raise forms.ValidationError("Please select at least one skill.")
        
        # Remove any leading/trailing commas and split
        skills_data = skills_data.strip(',')
        
        if not skills_data:
            raise forms.ValidationError("Please select at least one skill.")
        
        # Split the comma-separated string into individual IDs
        try:
            skill_ids = [int(sid.strip()) for sid in skills_data.split(',') if sid.strip()]
        except (ValueError, AttributeError) as e:
            print(f"DEBUG: Error parsing skills: {e}")
            print(f"DEBUG: skills_data = '{skills_data}'")
            raise forms.ValidationError("Invalid skill data format. Please try selecting your skills again.")
        
        if not skill_ids:
            raise forms.ValidationError("Please select at least one skill.")
        
        print(f"DEBUG: Parsed skill_ids: {skill_ids}")
        
        # Validate that all skill IDs exist in the database
        skills = Skill.objects.filter(id__in=skill_ids)
        
        if skills.count() != len(skill_ids):
            missing_ids = set(skill_ids) - set(skills.values_list('id', flat=True))
            print(f"DEBUG: Missing skill IDs: {missing_ids}")
            raise forms.ValidationError(f"Some selected skills are invalid (IDs: {missing_ids}).")
        
        print(f"DEBUG: Validated skills: {list(skills)}")
        
        return list(skills)  # Return list of Skill objects

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

# ----------------------------
#  Email Contact Form
# ----------------------------
class EmailContactForm(forms.Form):
    subject = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"placeholder": "Subject"}))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Write your message..."}))

    website = forms.CharField(required=False, widget=forms.HiddenInput)
    def clean(self):
        data = super().clean()
        if data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return data