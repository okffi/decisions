from django.conf.urls import url

from decisions.subscriptions.api import activitystream, mooncakestream

urlpatterns = [
    url(r'^as2/$', activitystream, name="api-activitystream"),
    url(r'^mooncake/$', mooncakestream, name="api-mooncakestream"),
]
