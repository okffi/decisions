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
from django.db.transaction import atomic

from decisions.subscriptions.models import (
    UserProfile,
    Subscription,
    SubscriptionUser,
    SubscriptionHit
)
from decisions.subscriptions.forms import (
    RegisterForm,
    LoginForm,
    SubscriptionForm,
    SubscriptionEditForm
)


@login_required
def dashboard(request):
    """
    Brief snippets of all interesting site features
    """
    all_subscriptions = SubscriptionUser.objects.filter(user=request.user)
    subscriptions = all_subscriptions.filter(active=True)
    inactive_subscriptions = all_subscriptions.filter(active=False)
    hits = (
        SubscriptionHit.objects
        .filter(notified_users=request.user)
        .order_by('-created')
        [:30]
    )

    for hit in hits:
        # intersect user's subscriptions and the hit's subscriptions
        hit_terms = [
            subscription.search_term
            for subscription in hit.subscriptions.all()
        ]
        user_terms = [
            subscription.search_term
            for subscription in request.user.subscription_set.all()
        ]
        terms = set(hit_terms).intersection(user_terms)
        hit.user_search_terms = terms

    for subscription in subscriptions:
        subscription.fresh_for_user = subscription.is_fresh(request.user)

    return render(
        request,
        "subscriptions/dashboard.html",
        {
            "subscriptions": subscriptions,
            "inactive_subscriptions": inactive_subscriptions,
            "feed": hits,
        })

@login_required
def subscriptions(request):
    """
    Detailed subscription management page

    TODO: More detail
    """
    all_subscriptions = SubscriptionUser.objects.filter(user=request.user)
    subscriptions = all_subscriptions.filter(active=True)
    inactive_subscriptions = all_subscriptions.filter(active=False)
    for subscription in subscriptions:
        subscription.fresh_for_user = subscription.is_fresh(request.user)

    return render(
        request,
        "subscriptions/subscriptions.html",
        {
            "subscriptions": subscriptions,
            "inactive_subscriptions": inactive_subscriptions,
        })

@login_required
def feed(request):
    """
    Detailed feed browsing pages

    TODO: paginate and allow browsing all of the feed
    """
    hits = (
        SubscriptionHit.objects
        .filter(notified_users=request.user)
        .order_by('-created')
        [:30]
    )

    for hit in hits:
        # intersect user's subscriptions and the hit's subscriptions
        hit_terms = [
            subscription.search_term
            for subscription in hit.subscriptions.all()
        ]
        user_terms = [
            subscription.search_term
            for subscription in request.user.subscription_set.all()
        ]
        terms = set(hit_terms).intersection(user_terms)
        hit.user_search_terms = terms

    return render(
        request,
        "subscriptions/feed.html",
        {
            "feed": hits,
        })


@login_required
def add_subscription(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            with atomic():
                subscription, created = (
                    Subscription.objects.get_or_create(
                        search_term=form.cleaned_data['search_term']
                    )
                )
                SubscriptionUser.objects.get_or_create(
                    subscription=subscription,
                    user=request.user,
                    defaults={
                        "send_mail": form.cleaned_data['send_mail']
                    }
                )

            messages.success(
                request,
                _("You have subscribed to the search term <tt>%(search_term)s</tt>") % form.cleaned_data)
            return redirect("subscriptions")
    else:
        form = SubscriptionForm(initial={"search_term": request.GET.get("q")})

    return render(request, "form.html", {"form": form, "verb": _("Subscribe")})

@login_required
def edit_subscription(request, subscription_id):
    usersub = get_object_or_404(
        SubscriptionUser,
        pk=subscription_id,
        user=request.user
    )

    if request.method == "POST":
        form = SubscriptionEditForm(request.POST)
        if form.is_valid():
            with atomic():
                # handle changed terms
                if form.cleaned_data["search_term"] != usersub.subscription.search_term:
                    subscription, created = (
                        Subscription.objects.get_or_create(
                            search_term=form.cleaned_data['search_term'],
                            defaults={
                                "previous_version": usersub.subscription
                            }
                        )
                    )
                    usersub.subscription = subscription

                usersub.send_mail = form.cleaned_data['send_mail']
                usersub.active = form.cleaned_data['active']
                usersub.save()

            messages.success(
                request,
                _("You have edited your subscription to <tt>%(search_term)s</tt>") % form.cleaned_data)

            return redirect("subscriptions")
    else:
        form = SubscriptionEditForm(initial={
            "search_term": usersub.subscription.search_term,
            "send_mail": usersub.send_mail,
            "active": usersub.active
        })

    return render(request, "form.html", {
        "form": form,
        "verb": _("Edit subscription")
    })



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

def suggest(request):
    """returns a list of suggest results in json

    currently it only finds and suggests fresh subscriptions
    """

    q = request.GET.get("q")

    if q is None:
        return JsonResponse([])

    fresh_subscriptions = (
        Subscription.objects
        .get_fresh()
        .filter(search_term__startswith=q)
    )[:5]

    ret = [sub.search_term for sub in fresh_subscriptions]

    return JsonResponse(ret)

def profile(request, username):
    return render(
        request,
        "account/profile.html",
        {"profile_user": get_object_or_404(User, username=username)}
    )

def edit_profile(request):
    return render(request, "account/edit_profile.html")
