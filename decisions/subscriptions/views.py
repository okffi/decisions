from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
    authenticate
)
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.utils.timezone import now

from decisions.subscriptions.models import UserProfile
from decisions.subscriptions.forms import RegisterForm, LoginForm


@login_required
def dashboard(request):
    return render(request, "subscriptions/dashboard.html")

def login(request):
    # TODO: add safe ?next= handling
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            if form.user is not None:
                if form.user.is_active:
                    auth_login(request, form.user)
                    messages.add_message(
                        request, messages.SUCCESS,
                        _("Logged in successfully"))
                    return redirect('dashboard')
                else:
                    messages.add_message(
                        request, messages.ERROR,
                        _("Your account is disabled. Please contact webmaster."))
    else:
        form = LoginForm(request.POST)

    return render(request, "form.html", {"form": form, "verb": _("Log in")})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"]
            )
            user.set_password(form.cleaned_data["password"])
            user.save()
            profile = UserProfile.objects.create(
                user=user,
                email_confirm_sent_on=now()
            )

            authenticated_user = authenticate(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"]
            )
            auth_login(request, authenticated_user)

            send_mail(
                _("Confirm your %(site)s registration") % {"site": settings.SITE_NAME},
                render_to_string("subscriptions/emails/confirm_email.txt", {
                    "confirm_code": profile.email_confirm_code,
                    "SITE_NAME": settings.SITE_NAME,
                    "SITE_URL": settings.SITE_URL,
                }),
                settings.DEFAULT_FROM_EMAIL,
                [form.cleaned_data["email"]]
            )


            messages.add_message(
                request, messages.SUCCESS,
                _("Your account has been registered. Check your mail to confirm your email address.")
            )
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, "form.html", {"form": form, "verb": _("Register")})

def confirm_email(request, confirm_code):
    try:
        user = User.objects.get(
            profile__email_confirmed__isnull=True,
            profile__email_confirm_code=confirm_code,
            profile__email_confirm_sent_on__gte=now() - timedelta(days=2)
        )
    except User.DoesNotExist:
        return render(request, "subscriptions/not_confirmed.html")

    user.profile.email_confirmed = now()
    user.profile.save()

    messages.add_message(
        request, messages.SUCCESS,
        _("Your email address has been confirmed.")
    )

    # XXX user might not be logged in
    return redirect("dashboard")

def logout(request):
    auth_logout(request)
    messages.add_message(
        request, messages.SUCCESS,
        _("You have logged out.")
    )
    return redirect("index")
