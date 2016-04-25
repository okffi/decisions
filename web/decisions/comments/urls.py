from django.conf.urls import url

from decisions.comments.views import get_comments, comment


urlpatterns = [
    url(r'^c/(?P<model_slug>[\w-]+)/(?P<object_id>\d+)/$', get_comments, name="get-comments"),
    url(r"^post/(?P<model_slug>[\w-]+)/(?P<object_id>\d+)/$", comment, name="post-comment"),
]
