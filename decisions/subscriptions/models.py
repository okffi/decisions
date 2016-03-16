from __future__ import unicode_literals

import os
import base64
from datetime import timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

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

    def is_fresh(self):
        return self.subscription.subscriptionhit_set.filter(
            created__gt=now()-timedelta(days=3)
        ).count()

    class Meta:
        verbose_name = _("subscribed user")
        verbose_name_plural = _("subscribed users")

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

    def __unicode__(self):
        return self.search_term

    class Meta:
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")


class SubscriptionHit(models.Model):
    subscriptions = models.ManyToManyField(Subscription)
    created = models.DateTimeField(default=now)
    subject = models.CharField(max_length=300)
    link = models.CharField(max_length=300)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    hit = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = _("subscription hit")
        verbose_name_plural = _("subscription hits")
        get_latest_by = "created"
