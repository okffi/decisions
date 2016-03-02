from __future__ import unicode_literals

import operator

from django.db import models
from django.db.models import Q
from django.contrib.postgres import fields as pgfields
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import get_default_timezone
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from dateutil.parser import parse

from decisions.ahjo.utils import b36encode


class AgendaItemQuerySet(models.QuerySet):
    def create_from_json(self, json):
        "json object -> AgendaItem object"

        if json["last_modified_time"]:
            last_modified_time = parse(json["last_modified_time"])
            last_modified_time = last_modified_time.replace(
                tzinfo=get_default_timezone()
            )
        else:
            last_modified_time = None

        return self.create(
            ahjo_id=json["id"],
            subject=json["subject"],
            preparer=json.get("preparer"),
            resolution=json["resolution"] or UNKNOWN,
            classification_code=json.get("classification_code"),
            last_modified_time=last_modified_time,
            original=json
        )
    create_from_json.queryset_only = False

    def textsearch(self, needle):
        possibilities = [
            Q(subject__contains=needle),
            # these do nothing
            #Q(original__issue__summary=needle),
            #Q(original__issue__category_name=needle)
        ]
        return self.filter(reduce(operator.or_, possibilities))


# From: https://github.com/City-of-Helsinki/openahjo/blob/master/ahjodoc/models.py#L196
# Update as necessary
PASSED = "PASSED_UNCHANGED"
PASSED_VOTED = "PASSED_VOTED"
PASSED_REVISED = "PASSED_REVISED"
PASSED_MODIFIED = "PASSED_MODIFIED"
REJECTED = "REJECTED"
NOTED = "NOTED"
RETURNED = "RETURNED"
REMOVED = "REMOVED"
TABLED = "TABLED"
ELECTION = "ELECTION"
UNKNOWN = "UNKNOWN" # Replaces NULL
RESOLUTION_CHOICES = (
    (PASSED, _('Passed as drafted')),
    (PASSED_VOTED, _('Passed after a vote')),
    (PASSED_REVISED, _('Passed revised by presenter')),
    (PASSED_MODIFIED, _('Passed modified')),
    (REJECTED, _('Rejected')),
    (NOTED, _('Noted as informational')),
    (RETURNED, _('Returned to preparation')),
    (REMOVED, _('Removed from agenda')),
    (TABLED, _('Tabled')),
    (ELECTION, _('Election')),
    (UNKNOWN, _('Unknown')),
)


class AgendaItem(models.Model):
    ahjo_id = models.IntegerField(db_index=True, unique=True)
    subject = models.CharField(
        # one line, yeah right
        max_length=500,
        verbose_name=_("Subject"),
    )
    preparer = models.CharField(
        max_length=100,
        verbose_name=_("Preparer"),
        null=True
    )
    resolution = models.CharField(
        max_length=20,
        choices=RESOLUTION_CHOICES,
        verbose_name=_("Resolution")
    )
    classification_code = models.CharField(
        max_length=20,
        verbose_name=_("Classification code"),
        null=True
    )
    last_modified_time = models.DateTimeField(
        verbose_name=_("Last modified time"),
        null=True
    )
    original = pgfields.JSONField()

    objects = AgendaItemQuerySet.as_manager()

    class Meta:
        verbose_name = _("agenda item")
        verbose_name_plural = _("agenda items")
        get_latest_by = "last_modified_time"

    def get_absolute_url(self):
        return reverse('ahjo-view',
                       kwargs={
                           "ahjo_id_b36": b36encode(self.ahjo_id),
                           "slug": slugify(self.subject)
                       })
