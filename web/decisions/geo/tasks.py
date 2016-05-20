import datetime

from django.utils.timezone import now

from decisions.celery import app
from decisions.geo import GEO_MODELS
from decisions.geo.models import PointIndex, PolygonIndex

def recreate_geoindex():
    PointIndex.objects.all().delete()
    PolygonIndex.objects.all().delete()
    for model in GEO_MODELS:
        create_points(model.objects.filter_points())
        create_polygons(model.objects.filter_polygons())

@app.task()
def update_geoindex(point_date=None, polygon_date=None):
    "look up new registered models with geodata and add them to the index"

    if point_date is None:
        try:
            point_date = PointIndex.objects.latest().content_date
        except PointIndex.DoesNotExist:
            point_date = now() - datetime.timedelta(days=28)

    if polygon_date is None:
        try:
            polygon_date = PolygonIndex.objects.latest().content_date
        except PolygonIndex.DoesNotExist:
            polygon_date = now() - datetime.timedelta(days=28)

    for model in GEO_MODELS:
        new_points = model.objects.filter(**{
                model._meta.get_latest_by + "__gt": point_date
        }).filter_points()
        create_points(new_points)

        new_polygons = model.objects.filter(**{
                model._meta.get_latest_by + "__gt": polygon_date
        }).filter_polygons()
        create_polygons(new_polygons)

def create_points(new_points):
    for obj, point in new_points:
        PointIndex.objects.create(
            content_object=obj,
            point=point,
            title=unicode(obj),
            description=obj.get_summary(),
            content_date=obj.get_content_date(),
        )

def create_polygons(new_polygons):
    for obj, polygon in new_polygons:
        PolygonIndex.objects.create(
            content_object=obj,
            polygon=polygon,
            title=unicode(obj),
            description=obj.get_summary(),
            content_date=obj.get_content_date()
        )
