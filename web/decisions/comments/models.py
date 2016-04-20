from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils.timezone import now

import arrow


class Comment(models.Model):
    user = models.ForeignKey(User, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

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
