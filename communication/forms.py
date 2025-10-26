from django import forms

class EmailContactForm(forms.Form):
    subject = forms.CharField(max_length=120)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 6}))
    website = forms.CharField(required=False, widget=forms.HiddenInput)  # honeypot

    def clean(self):
        data = super().clean()
        if data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return data

class SendMessageForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))