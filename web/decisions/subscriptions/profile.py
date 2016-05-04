"The profile and user management related views"

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
    authenticate
)
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.utils.timezone import now
from django.utils.http import is_safe_url
from django.template.loader import render_to_string
from django.core.cache import cache

from decisions.subscriptions.forms import (
    LoginForm, RegisterForm,
    ForgotPasswordForm, ChangePasswordForm, ResetPasswordForm
)
from decisions.subscriptions.models import UserProfile, make_confirm_code

def login(request):
    redirect_to = request.POST.get("next",
                                   request.GET.get("next", ''))

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            if form.user is not None:
                if form.user.is_active:
                    auth_login(request, form.user)
                    messages.add_message(
                        request, messages.SUCCESS,
                        _("Logged in successfully"))
                    if not is_safe_url(url=redirect_to,
                                       host=request.get_host()):
                        return redirect("index")

                    return redirect(redirect_to)
                else:
                    messages.add_message(
                        request, messages.ERROR,
                        _("Your account is disabled. Please contact webmaster."))
    else:
        form = LoginForm(initial={"next": redirect_to})

    return render(request, "account/login.html", {
        "form": form,
        "next": redirect_to,
    })

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
            return redirect('index')
    else:
        form = RegisterForm()

    return render(request, "form.html", {"form": form, "verb": _("Register")})

def login_or_register(request):
    return render(request, "account/login_or_register.html", {
        "login_form": LoginForm(),
        "register_form": RegisterForm(),
    })

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

    return redirect("index")

def logout(request):
    auth_logout(request)
    messages.add_message(
        request, messages.SUCCESS,
        _("You have logged out.")
    )
    return redirect("index")

def profile(request, username):
    return render(
        request,
        "account/profile.html",
        {"profile_user": get_object_or_404(User, username=username)}
    )

@login_required
def edit_profile(request):
    return render(request, "account/edit_profile.html")

def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Don't send resets too often
            recent_reset = cache.get("recent-reset-codes-%s" % email)
            if recent_reset and recent_reset > now() - timedelta(days=2):
                recent_ok = False
            else:
                recent_ok = True

            # Only send mail to addresses we know
            if User.objects.filter(email=email, is_active=True).count():
                email_ok = True
            else:
                email_ok = False

            # Process the request only if checks pass
            if recent_ok and email_ok:
                reset_code = make_confirm_code()
                valid_time = 4 * 3600 # seconds
                cache.set("password-code-%s" % reset_code, email, valid_time)
                cache.set("recent-reset-codes-%s" % email, now(), valid_time)

                send_mail(
                    _("Password reset for %(site)s") % {"site": settings.SITE_NAME},
                    render_to_string("subscriptions/emails/reset_password.txt", {
                        "confirm_code": reset_code,
                        "SITE_NAME": settings.SITE_NAME,
                    "SITE_URL": settings.SITE_URL,
                    }),
                    settings.DEFAULT_FROM_EMAIL,
                    [email]
                )

            # We will never give feedback on whether we actually have
            # that email address in our database. Pretend we actually
            # did something in any case.
            messages.add_message(request, messages.SUCCESS, _("We have now sent reset instructions."))
            return redirect("index")
    else:
        form = ForgotPasswordForm()

    return render(request, "account/forgot_password.html", {"form": form})

def reset_password(request, reset_code):
    email = cache.get("password-code-%s" % reset_code)
    if not email:
        return render(request, "account/reset_invalid.html")

    # We're reasonably guaranteed the email exists at this point.
    user = User.objects.get(email=email, is_active=True)
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password"])
            user.save()
            messages.add_message(
                request, messages.SUCCESS,
                _("Great! You have reset your password. You can now log in using your new password."))
            return redirect("index")
    else:
        form = ResetPasswordForm()

    return render(request, "account/reset_password.html", {"form": form})

@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.save()
            messages.add_message(request, messages.SUCCESS, _("You have changed your password successfully."))
            return redirect("index")
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, "account/change_password.html", {"form": form})
