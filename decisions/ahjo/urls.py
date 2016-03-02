from django.conf.urls import url

from decisions.ahjo.views import search, view

urlpatterns = [
    url("^$", search, name="ahjo-search"),
    url("^decision/(?P<ahjo_id_b36>\w+)/(?P<slug>[\w-]+)/$", view, name="ahjo-view"),
    url("^d/(?P<ahjo_id_b36>\w+)/$", view, name="ahjo-short"),
]
