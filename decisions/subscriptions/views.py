from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
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
from django.utils.http import is_safe_url

from decisions.subscriptions.models import (
    UserProfile,
    Subscription,
    SubscriptionHit
)
from decisions.subscriptions.forms import (
    RegisterForm,
    LoginForm,
    SubscriptionForm
)


@login_required
def dashboard(request):
    subscriptions = Subscription.objects.filter(user=request.user)
    hits = (
        SubscriptionHit.objects
        .filter(subscription__user=request.user)
        .order_by('-created')
        .distinct("link")
        [:30]
    )

    return render(
        request,
        "subscriptions/dashboard.html",
        {
            "subscriptions": subscriptions,
            "feed": hits,
        })

@login_required
def add_subscription(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(
                request,
                _("You have subscribed to the search term <tt>%(search_term)s</tt>") % form.cleaned_data)
            return redirect("dashboard")
    else:
        form = SubscriptionForm(initial={"search_term": request.GET.get("q")})

    return render(request, "form.html", {"form": form, "verb": _("Subscribe")})

@login_required
def edit_subscription(request, subscription_id):
    subscription = get_object_or_404(
        Subscription,
        pk=subscription_id,
        user=request.user
    )

    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            obj = form.save()
            messages.success(
                request,
                _("You have edited the search term <tt>%(search_term)s</tt>") % form.cleaned_data)
            return redirect("dashboard")
    else:
        form = SubscriptionForm(instance=subscription)

    return render(request, "form.html", {"form": form, "verb": _("Edit subscription")})



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
                        return redirect("dashboard")

                    return redirect(redirect_to)
                else:
                    messages.add_message(
                        request, messages.ERROR,
                        _("Your account is disabled. Please contact webmaster."))
    else:
        form = LoginForm(initial={"next": redirect_to})

    return render(request, "form.html", {
        "form": form,
        "verb": _("Log in"),
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
