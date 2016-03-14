from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ungettext
from django.template import loader
from django.core.mail import send_mail

from haystack.query import SearchQuerySet

from decisions.subscriptions.models import Subscription, SubscriptionHit


def process_subscriptions():
    """Loop over all active subscriptions and create new hits based on
    search results"""

    active_subs = Subscription.objects.filter(active=True)
    notify_users = set()
    time_started = now()
    hit_count = 0

    for s in active_subs:
        try:
            last_hit_date = s.subscriptionhit_set.latest().created
        except SubscriptionHit.DoesNotExist:
            last_hit_date = s.created

        results = (
            SearchQuerySet()
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
        for hit,created in hits:
            hit.subscriptions.add(s)

        hit_count += len(hits)

        if s.send_mail and hits:
            notify_users.update(
                s.subscribers.filter(
                    profile__email_confirmed__isnull=False
                )
            )

    for u in notify_users:
        notifications = (
            SubscriptionHit.objects
            .filter(
                created__gte=time_started,
                subscription__subscribers=u,
                subscription__send_mail=True,
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
