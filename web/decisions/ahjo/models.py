from __future__ import unicode_literals

import operator

from django.db import models
from django.db.models import Q, Count
from django.contrib.postgres import fields as pgfields
from django.utils.translation import ugettext_lazy as _, get_language
from django.utils.timezone import get_default_timezone, now
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify, linebreaks, escape
from django.contrib.auth.models import User

from dateutil.parser import parse
import arrow
from pytz import timezone, UTC
from tagging.registry import register as tagging_register
from tagging.models import Tag
from tagging.utils import calculate_cloud

from decisions.ahjo.utils import b36encode, b36decode


AHJO_TZ = timezone('Europe/Helsinki')
AHJO_PREFIX = "http://dev.hel.fi"


class AgendaItemQuerySet(models.QuerySet):
    def create_from_json(self, json):
        "json object -> AgendaItem object"

        if json["last_modified_time"]:
            last_modified_time = parse(json["last_modified_time"])
            last_modified_time = last_modified_time.replace(
                tzinfo=AHJO_TZ
            )
        else:
            last_modified_time = None

        if self.filter(ahjo_id=json["id"]).count():
            has_revisions = True
        else:
            has_revisions = False

        return self.create(
            ahjo_id=json["id"],
            subject=json["subject"],
            preparer=json.get("preparer"),
            resolution=json["resolution"] or UNKNOWN,
            classification_code=json.get("classification_code"),
            last_modified_time=last_modified_time,
            original=json,
            has_revisions=has_revisions
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

# Section types can apparently be as follows. Mark for translation
SECTION_TYPE_MAP = {
    "resolution": _("Resolution"),
    "summary": _("Summary"),
    "presenter": _("Presenter"),
    "hearing": _("Hearing"),
    "reasons for resolution": _("Reasons for resolution"),
    "draft resolution": _("Draft resolution"),
    "default": _("Section: %(section_type)s"),
}

class AgendaItem(models.Model):
    ahjo_id = models.IntegerField(db_index=True)
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
    fetched = models.DateTimeField(default=now)
    original = pgfields.JSONField(verbose_name=_("Original"))
    has_revisions = models.BooleanField(default=False)

    objects = AgendaItemQuerySet.as_manager()

    def has_geometry(self):
        return self.original["issue"]["geometries"]

    def title(self):
        return self.subject

    __unicode__ = title

    class Meta:
        verbose_name = _("agenda item")
        verbose_name_plural = _("agenda items")
        get_latest_by = "last_modified_time"
        ordering = ("-last_modified_time",)

    def get_absolute_url(self):
        if self.has_revisions:
            return reverse('ahjo-view',
                           kwargs={
                               "ahjo_id_b36": b36encode(self.ahjo_id),
                               "slug": slugify(self.subject),
                               "disambiguation_id": self.pk
                           })
        else:
            return reverse('ahjo-view',
                           kwargs={
                               "ahjo_id_b36": b36encode(self.ahjo_id),
                               "slug": slugify(self.subject)
                           })

    def get_attachments(self):
        return [v for v in self.original["attachments"]
                if all([v["name"], v["file_uri"], v["file_type"]])]

    def resolve_url(self, url):
        return AHJO_PREFIX + url

    def get_activitystream(self):
        """Activity stream object for this item

        Some fields are duplicated because mooncake doesn't seem to
        strictly follow the standard.

        """
        policy_url = self.resolve_url(self.original['meeting']['policymaker'])
        object_url = self.resolve_url(self.original['resource_uri'])
        target_url = self.resolve_url(self.original['issue']['resource_uri'])

        return {
            "@context": "http://www.w3.org/ns/activitystreams",
            "@type": "Add",
            "type": "Add",
            # output UTC
            "published": (
                self.last_modified_time
                .astimezone(UTC)
                .replace(microsecond=0)
                .isoformat()
            ),
            "actor": {
                "@type": "Group",
                "type": "Group",
                "@id": policy_url,
                "id": policy_url,
                "displayName": self.original["meeting"]["policymaker_name"],
            },
            "object": {
                "@id": object_url,
                "id": object_url,
                "@type": "Content",
                "type": "Content",
                "url": self.original["permalink"],
                "displayName": self.subject,
                "content": self.get_content_intro(),
            },
            "target": {
                "@id": target_url,
                "id": target_url,
                "@type": "Content",
                "type": "Content",
                "displayName": self.original["issue"]["subject"],
                "content": self.original["issue"].get("summary")
            }
        }

    def get_content_intro(self):
        if self.original["content"]:
            return self.original["content"][0]["text"]
        return u""

    def generate_tags(self):
        "scours the instance data for useful tags"
        tags = set()

        keys = [
            ["classification_description"],
            ["preparer"],
            ["introducer"],
            ["issue", "category_name"],
            ["meeting", "policymaker_name"]
        ]
        for key in keys:
            value = self.original
            try:
                for part in key:
                    value = value[part]
                if value is not None:
                    tags.add("#" + slugify(value)[:49])
            except KeyError:
                continue

        for t in tags:
            Tag.objects.add_tag(self, t)

        return self.tags

    def tag_cloud(self):
        "Returns instance tags annotated with tag cloud weights"
        # Just using self.tags doesn't aggregate properly (the only
        # matching item is self)
        tags = (Tag.objects
                .filter(pk__in=[t.pk for t in self.tags])
                .annotate(count=Count('items')))
        return calculate_cloud(tags)

tagging_register(AgendaItem)


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
            "text": linebreaks(escape(self.text)),
            "created_timestamp": self.created.isoformat(),
            "created": arrow.get(self.created).humanize(locale=get_language())
        }
