from django.conf.urls import url

from decisions.ahjo.views import view, comment, get_comments


urlpatterns = [
    url("^decision/(?P<ahjo_id_b36>\w+)/(?P<slug>[\w-]+)/$", view, name="ahjo-view"),
    url("^d/(?P<ahjo_id_b36>\w+)/$", view, name="ahjo-short"),
    url("^comment/(?P<ahjo_id_b36>\w+)/$", comment, name="ahjo-comment"),
    url("^get-comments/(?P<ahjo_id_b36>\w+)/$", get_comments, name="ahjo-get-comments"),
]
