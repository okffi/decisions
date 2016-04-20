from django.conf.urls import url

from decisions.subscriptions.views import (
    add_subscription,
    edit_subscription,
    suggest,
    feed,
    public_feed,
    subscriptions,
)


urlpatterns = [
    url(r'^$', subscriptions, name="subscriptions"),
    url(r'^feed/$', feed, name="feed"),
    url(r'^public-feed/$', public_feed, name="public-feed"),
    url(r'^add/$', add_subscription, name="add-subscription"),
    url(r'^edit/(?P<subscription_id>\d+)/$', edit_subscription, name="edit-subscription"),
    url(r'^suggest/$', suggest, name='suggest'),
]
