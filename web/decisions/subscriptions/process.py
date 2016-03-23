from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ungettext
from django.template import loader
from django.core.mail import send_mail
from django.db.transaction import atomic

from haystack.query import SearchQuerySet

from decisions.subscriptions.models import Subscription, SubscriptionHit
from decisions.subscriptions.voikko import VoikkoSearchQuerySet

@atomic
def process_subscriptions():
    """Loop over all active subscriptions and create new hits based on
    search results"""

    # TODO: don't process subscriptions that don't have any active
    # user subscriptions
    active_subs = Subscription.objects.all()
    notify_users = set()
    time_started = now()
    hit_count = 0

    for s in active_subs:
        try:
            last_hit_date = s.subscriptionhit_set.latest().created
        except SubscriptionHit.DoesNotExist:
            last_hit_date = s.created

        results = (
            VoikkoSearchQuerySet()
            .auto_query(s.search_term)
            .filter(pub_date__gt=last_hit_date)
            .load_all()
        )

        hits = [
            SubscriptionHit.objects.get_or_create(
                subject=r.subject,
                link=r.object.get_absolute_url(),
                defaults={"hit": r.object}
            )
            for r in results
        ]
        for hit, created in hits:
            hit.subscriptions.add(s)

        hit_count += len(hits)

        if hits:
            users = s.subscribed_users.filter(
                subscriptionuser__active=True,
                subscriptionuser__send_mail=True,
                profile__email_confirmed__isnull=False
            )

            for hit, created in hits:
                hit.notified_users.add(*users)

            notify_users.update(users)

    for u in notify_users:
        notifications = (
            SubscriptionHit.objects
            .filter(
                created__gte=time_started,
                notified_users=u
            )
            .order_by('-created')
        )
        notify_count = notifications.count()
        notifications = notifications[:10]

        # TODO activate user's preferred language here
        send_mail(
            ungettext(
                "[%(SITE_NAME)s] %(event_count)s new event",
                "[%(SITE_NAME)s] %(event_count)s new events",
                notify_count
            ) % {
                "SITE_NAME": settings.SITE_NAME,
                "event_count": notify_count,
            },
            loader.get_template("subscriptions/emails/new_events.txt").render({
                    "notifications": notifications,
                    "more_notifications": max(0, notify_count-10),
                    "user": u,
                    "SITE_URL": settings.SITE_URL,
                    "SITE_NAME": settings.SITE_NAME,
                }),
            settings.DEFAULT_FROM_EMAIL,
            [u.email],
        )

    return hit_count
