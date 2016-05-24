from __future__ import unicode_literals

import os
import base64
from datetime import timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres import fields as pgfields

def make_confirm_code():
    return base64.b64encode(os.urandom(15))


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', related_name="profile")
    email_confirmed = models.DateTimeField(null=True, blank=True)
    email_confirm_code = models.CharField(
        max_length=20,
        default=make_confirm_code
    )
    email_confirm_sent_on = models.DateTimeField(null=True, blank=True)

    extra = pgfields.JSONField(default=dict)

    def __unicode__(self):
        return self.user.username

    def confirmed_email(self):
        if self.email_confirmed:
            return self.user.email

class SubscriptionUser(models.Model):
    user = models.ForeignKey('auth.User')
    subscription = models.ForeignKey('Subscription')
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    send_mail = models.BooleanField(
        default=False,
        verbose_name=_('Sends email')
    )
    subscribed_at = models.DateTimeField(default=now)

    def __unicode__(self):
        return u"%s: %s" % (self.user, self.subscription)

    def is_fresh(self, for_user):
        return self.subscription.subscriptionhit_set.filter(
            created__gt=now()-timedelta(days=3),
            notified_users=for_user
        ).count()

    class Meta:
        verbose_name = _("subscribed user")
        verbose_name_plural = _("subscribed users")

class SubscriptionQuerySet(models.QuerySet):
    def get_fresh(self):
        return (
            self
            .filter(
                subscriptionhit__created__gt=now()-timedelta(days=3)
            )
            .annotate(hit_count=models.Count('subscriptionhit'))
            .filter(hit_count__gt=0)
        )

class Subscription(models.Model):
    subscribed_users = models.ManyToManyField(
        'auth.User',
        through=SubscriptionUser
    )
    previous_version = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name="next_versions"
    )
    search_term = models.CharField(
        max_length=300,
        verbose_name=_('Search term')
    )
    created = models.DateTimeField(default=now)

    objects = SubscriptionQuerySet.as_manager()

    def __unicode__(self):
        return self.search_term

    class Meta:
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")



class SubscriptionHit(models.Model):
    subscriptions = models.ManyToManyField(Subscription)
    notified_users = models.ManyToManyField('auth.User')
    created = models.DateTimeField(default=now)
    subject = models.CharField(max_length=300)
    link = models.CharField(max_length=300)

    SEARCH_RESULT, COMMENT_REPLY = range(2)
    HIT_TYPES = (
        (SEARCH_RESULT, _("Search result")),
        (COMMENT_REPLY, _("Comment reply")),
    )

    hit_type = models.IntegerField(default=SEARCH_RESULT, choices=HIT_TYPES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    hit = GenericForeignKey('content_type', 'object_id')
    extra = pgfields.JSONField(default=dict)

    # utility functions to allow template checks
    def is_comment_reply(self):
        return self.hit_type == self.COMMENT_REPLY

    def is_search_result(self):
        return self.hit_type == self.SEARCH_RESULT

    def format_subject(self):
        "translated, formatted subject line"
        if "subject_mapping" in self.extra:
            return _(self.subject) % self.extra["subject_mapping"]
        return self.subject

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = _("subscription hit")
        verbose_name_plural = _("subscription hits")
        get_latest_by = "created"
        ordering = ('-created',)
