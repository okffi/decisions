from django.shortcuts import render
from django.http import JsonResponse

from decisions.geo.models import PointIndex, PolygonIndex

def map_search(request):
    """Search for things in the index that are

    - Near the given location (reverse geocode it!) javascript?
    - Within the given perimeter (e.g. 3km)
    - Reasonably recent
    """

    return render(request, "geo/map_search.html")


def get_things_near_point(point, distance=D(km=5)):
    points = (
        PointIndex.objects.filter(point__distance_lte=(point, distance))
    )
    polygons = (
        PolygonIndex.objects.filter(polygon__distance_lte=(point, distance))
    )
    return {
        "points": points,
        "polygons": polygons,
    }

def get_things(request):
    latlon = request.GET.get("lat", 60), request.GET.get("lon", 25)
    distance = D(km=request.GET.get("dist", 5))

    return JsonResponse(get_things_near_point(latlon))
