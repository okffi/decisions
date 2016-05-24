"Subscriptions related views"

from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db.transaction import atomic
from django.http import JsonResponse

from tagging.utils import calculate_cloud

from decisions.subscriptions.models import (
    Subscription,
    SubscriptionUser,
    SubscriptionHit
)
from decisions.subscriptions.forms import (
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
        subscription.count = max(1, subscription.is_fresh(request.user))
    subscriptions = calculate_cloud(subscriptions)

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

def public_feed(request):
    "Recent feed hits from everyone's saved searches"
    hits = (
        SubscriptionHit.objects
        .order_by('-created')
        [:30]
    )

    return render(
        request,
        "subscriptions/public_feed.html",
        {
            "feed": hits
        }
    )

@login_required
def add_subscription(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            with atomic():
                backend = form.cleaned_data['search_backend']
                if backend == Subscription.HAYSTACK:
                    subscription, created = (
                        Subscription.objects.get_or_create(
                            search_term=form.cleaned_data['search_term'],
                            search_backend=Subscription.HAYSTACK,
                        )
                    )
                elif backend == Subscription.GEO:
                    distance_m = form.cleaned_data['distance_meters']
                    point = form.point
                    subscription, created = (
                        Subscription.objects.get_or_create(
                            search_term=form.cleaned_data['search_term'],
                            search_backend=Subscription.GEO,
                            defaults={
                                "extra": {
                                    "point": list(point),
                                    "distance_meters": distance_m
                                }
                            }
                        )
                    )
                else:
                    raise RuntimeError("Unknown search backend %s provided" % backend)

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
        form = SubscriptionForm(initial={
            "search_term": request.GET.get("q"),
            "search_backend": request.GET.get("t")
        })

    return render(request, "subscriptions/subscription_form.html", {"form": form, "verb": _("Subscribe")})

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
                if (form.cleaned_data["search_term"] != usersub.subscription.search_term
                    or form.cleaned_data["search_backend"] != usersub.subscription.search_backend
                    or ("distance_meters" in usersub.subscription.extra and form.cleaned_data["distance_meters"] != usersub.subscription.extra["distance_meters"])):
                    defaults = {
                        "previous_version": usersub.subscription
                    }
                    if form.cleaned_data["search_backend"] == Subscription.GEO:
                        defaults.update(extra={
                            "point": list(form.point),
                            "distance_meters": form.cleaned_data["distance_meters"]
                        })
                        subscription, created = (
                            Subscription.objects.get_or_create(
                                search_term=form.cleaned_data['search_term'],
                                search_backend=form.cleaned_data['search_backend'],
                                extra__distance_meters=form.cleaned_data["distance_meters"],
                                defaults=defaults
                            )
                        )
                    elif form.cleaned_data["search_backend"] == Subscription.HAYSTACK:
                        subscription, created = (
                            Subscription.objects.get_or_create(
                                search_term=form.cleaned_data['search_term'],
                                search_backend=form.cleaned_data['search_backend'],
                                defaults=defaults
                            )
                        )
                    else:
                        raise RuntimeError("Unknown subscription type %s" % form.cleaned_data["search_backend"])
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
            "active": usersub.active,
            "search_backend": usersub.subscription.search_backend
        })

    return render(request, "subscriptions/subscription_form.html", {
        "form": form,
        "verb": _("Edit subscription")
    })

def suggest(request):
    """returns a list of suggest results in json

    currently it only finds and suggests fresh subscriptions
    """

    q = request.GET.get("q")

    if q is None:
        return JsonResponse([], safe=False)

    fresh_subscriptions = (
        Subscription.objects
        .get_fresh()
        .filter(search_term__startswith=q)
    )[:5]

    ret = [sub.search_term for sub in fresh_subscriptions]

    return JsonResponse(ret, safe=False)
