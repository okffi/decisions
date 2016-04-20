from django.conf.urls import url

from decisions.ahjo.views import view, comment, get_comments, get_geometry


urlpatterns = [
    url(r"^decision/(?P<ahjo_id_b36>\w+)/(?P<slug>[\w-]+)/$",
        view, name="ahjo-view"),
    url(r"^decision/(?P<ahjo_id_b36>\w+)/(?P<disambiguation_id>\d+)/(?P<slug>[\w-]+)/$",
        view, name="ahjo-view"),
    url(r"^d/(?P<ahjo_id_b36>\w+)/$", view, name="ahjo-short"),
    url(r"^comment/(?P<ahjo_id_b36>\w+)/(?P<disambiguation_id>\d+)/$", comment, name="ahjo-comment"),
    url(r"^get-comments/(?P<ahjo_id_b36>\w+)/(?P<disambiguation_id>\d+)/$", get_comments, name="ahjo-get-comments"),
    url(r'^get-geometry/(?P<agendaitem_id>\d+)/$', get_geometry, name="ahjo-get-geometry"),
]
