from django.conf.urls import url

from decisions.geo.views import geosearch, search_page


urlpatterns = [
    url(r'^$', search_page, name="geoindex"),
    url(r'^search/$', geosearch, name="geosearch"),
]
