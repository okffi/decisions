from django.conf.urls import url

from decisions.subscriptions.views import (
    login,
    dashboard,
    register,
    confirm_email,
    logout,
    add_subscription,
    edit_subscription,
    suggest
)


urlpatterns = [
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, name="logout"),
    url(r'^register/$', register, name="register"),
    url(r'^confirm/(?P<confirm_code>.+)/$', confirm_email, name="confirm-email"),
    url(r'^add/$', add_subscription, name="add-subscription"),
    url(r'^edit/(?P<subscription_id>\d+)/$', edit_subscription, name="edit-subscription"),
    url(r'^suggest/$', suggest, name='suggest'),
    url(r'^$', dashboard, name="dashboard"),
]
