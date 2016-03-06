from __future__ import unicode_literals

import operator

from django.db import models
from django.db.models import Q
from django.contrib.postgres import fields as pgfields
from django.utils.translation import ugettext_lazy as _, get_language
from django.utils.timezone import get_default_timezone, now
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User

from dateutil.parser import parse
import arrow

from decisions.ahjo.utils import b36encode, b36decode


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

    def get_b36(self, id_b36):
        return self.get(ahjo_id=b36decode(id_b36))

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
    original = pgfields.JSONField(verbose_name=_("Original"))

    objects = AgendaItemQuerySet.as_manager()

    def title(self):
        return self.subject

    __unicode__ = title

    class Meta:
        verbose_name = _("agenda item")
        verbose_name_plural = _("agenda items")
        get_latest_by = "last_modified_time"
        ordering = ("-last_modified_time",)

    def get_absolute_url(self):
        return reverse('ahjo-view',
                       kwargs={
                           "ahjo_id_b36": b36encode(self.ahjo_id),
                           "slug": slugify(self.subject)
                       })

    def get_attachments(self):
        return [v for v in self.original["attachments"]
                if all([v["name"], v["file_uri"], v["file_type"]])]


class Comment(models.Model):
    user = models.ForeignKey(User, null=True)
    agendaitem = models.ForeignKey(AgendaItem)
    selector = models.CharField(
        max_length=200,
        help_text=_("This is the element where the comment "
                    "attaches on a decision")
    )
    quote = models.TextField(
        verbose_name=_("Quote"),
        help_text=_("Quotes are required.")
    )
    text = models.TextField(
        verbose_name=_("Comment")
    )
    created = models.DateTimeField(default=now, editable=False)

    class Meta:
        verbose_name = _("comment")
        verbose_name_plural = _("comments")
        ordering = ("text",)

    def get_dict(self):
        return {
            "poster": self.user.username if self.user else _("guest"),
            "selector": self.selector,
            "text": self.text,
            "created_timestamp": self.created.isoformat(),
            "created": arrow.get(self.created).humanize(locale=get_language())
        }
