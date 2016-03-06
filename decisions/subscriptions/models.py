from __future__ import unicode_literals

import os
import base64

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now


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

class Subscription(models.Model):
    user = models.ForeignKey('auth.User')
    search_term = models.CharField(
        max_length=300,
        verbose_name=_('Search term')
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    created = models.DateTimeField(default=now)
    send_mail = models.BooleanField(
        default=False,
        verbose_name=_('Sends email')
    )
