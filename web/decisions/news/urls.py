from django.conf.urls import url

from decisions.news.views import entry

urlpatterns = [
    url('^(?P<year>\d{4})/(?P<object_id>\d+)-(?P<slug>[\w-]+)/$', entry, name="news-entry"),
]
