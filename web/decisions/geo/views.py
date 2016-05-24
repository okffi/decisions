import requests

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _

from decisions.geo.models import PointIndex, PolygonIndex

def search_page(request):
    """Main UI page for map search. Magic happens in javascript.
    """
    if request.GET.get("q"):
        # allow GET forms to search the map
        return HttpResponseRedirect(
            reverse("geoindex") + "#q=" + request.GET["q"]
        )

    return render(request, "geo/map_search.html")

def geosearch(request):
    place_name = request.GET.get("q", None)
    if not place_name:
        return JsonResponse({"status": "no query"})
    center = geocode(place_name)
    if not center:
        return JsonResponse({"status": "no results"})

    # geocode returns lat,lon but we store fields in lon,lat
    p = Point(
        center["coordinates"][1],
        center["coordinates"][0]
    )

    try:
        d_m = max(100, min(3000, int(request.GET["d"])))
    except (KeyError, ValueError):
        d_m = 1000
    d = D(m=d_m)

    things = get_things_near_point(
        point=p,
        distance=d
    )

    points = [
        {
            "coordinates": [p.point.y, p.point.x],
            "title": p.title,
            "description": p.description,
            "timesince": _("%(since)s ago") % {"since": timesince(p.content_date)},
            "link": p.content_object.get_absolute_url(),
        }
        for p in things["points"]
    ]

    polygons = [
        {
            "coordinates": [
                [[[y,x] for x,y in ring]
                 for ring in poly]
                for poly in mp.polygon],
            "title": mp.title,
            "description": mp.description,
            "timesince": _("%(since)s ago") % {"since": timesince(p.content_date)},
            "link": p.content_object.get_absolute_url(),
        }
        for mp in things["polygons"]
    ]

    return JsonResponse({
        "status": "ok",
        "center": center,
        "points": points,
        "polygons": polygons,
        "radius": d.m
    })

def geocode(place_name):
    place_name = place_name.strip().lower()

    geojson = cache.get("geocode-%s" % place_name)
    if geojson is None:
        geojson = requests.get(
            "http://api.digitransit.fi/geocoding/v1/search",
            params={
                "text": place_name,
                "size": 1,
                "boundary.circle.lat": 60.2,
                "boundary.circle.lon": 24.936,
                "boundary.circle.radius": 30,
            }
        ).json()

        cache.set("geocode-%s" % place_name, geojson)

    if geojson["features"]:
        feat = geojson["features"][0]
        lon, lat = feat["geometry"]["coordinates"]
        return {
            "coordinates": [lat, lon],
            "title": feat["properties"]["name"],
        }

    return {}


def get_things_near_point(point, distance=D(km=5)):
    points = (
        PointIndex.objects.filter(point__distance_lte=(point, distance))
    )[:50]
    polygons = (
        PolygonIndex.objects.filter(polygon__distance_lte=(point, distance))
    )[:50]
    return {
        "points": points,
        "polygons": polygons,
    }
