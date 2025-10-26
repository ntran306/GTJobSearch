from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from .forms import EmailContactForm
from .services import send_contact_email

User = get_user_model()


@login_required
def contact_user(request, user_id):
    recipient = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = EmailContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            try:
                send_contact_email(
                    to_email=recipient.email,
                    subject=subject,
                    message=message,
                    reply_to=request.user.email,
                )
                messages.success(request, f"Email successfully sent to {recipient.username}.")
                return redirect("accounts:view", user_id=recipient.id)
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
    else:
        form = EmailContactForm()

    return render(request, "communication/contact_user.html", {
        "form": form,
        "recipient": recipient,
    })