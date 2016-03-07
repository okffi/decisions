from django.conf.urls import url

from decisions.subscriptions.views import (
    login,
    dashboard,
    register,
    confirm_email,
    logout,
    add_subscription,
    edit_subscription
)


urlpatterns = [
    url('^login/$', login, name="login"),
    url('^logout/$', logout, name="logout"),
    url('^register/$', register, name="register"),
    url('^confirm/(?P<confirm_code>.+)/$', confirm_email, name="confirm-email"),
    url('^add/$', add_subscription, name="add-subscription"),
    url('^edit/(?P<subscription_id>\d+)/$', edit_subscription, name="edit-subscription"),
    url('^$', dashboard, name="dashboard"),
]
