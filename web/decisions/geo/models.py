from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class PointIndex(models.Model):
    "geographical point lookup"
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    point = models.PointField(geography=True)

    title = models.CharField(max_length=255)
    description = models.TextField()
    content_date = models.DateTimeField()

    def __unicode__(self):
        return self.title

    class Meta:
        get_latest_by = "content_date"
        ordering = ("-content_date",)

class PolygonIndex(models.Model):
    "geographical area lookup"
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    polygon = models.MultiPolygonField(geography=True)

    title = models.CharField(max_length=255)
    description = models.TextField()
    content_date = models.DateTimeField()

    def __unicode__(self):
        return self.title

    class Meta:
        get_latest_by = "content_date"
        ordering = ("-content_date",)
