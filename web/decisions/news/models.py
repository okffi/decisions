from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

LANGUAGES = [(k, _(v)) for k,v in settings.LANGUAGES]


class Entry(models.Model):
    # Anonymous entries are considered written by the site itself
    author = models.ForeignKey('auth.User', null=True, blank=True)
    pub_date = models.DateTimeField(default=now)
    language = models.CharField(max_length=5, choices=LANGUAGES, default=settings.LANGUAGE_CODE)
    subject = models.CharField(max_length=50)
    slug = models.SlugField()
    text = models.TextField()

    def __unicode__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse('news-entry', kwargs={"year": self.pub_date.year, "object_id": self.pk, "slug": self.slug})

    class Meta:
        verbose_name = _("Entry")
        verbose_name_plural = _("Entries")
