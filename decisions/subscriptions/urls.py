from django.conf.urls import url

from decisions.subscriptions.views import (
    login,
    dashboard,
    register,
    confirm_email,
    logout
)


urlpatterns = [
    url('^login/$', login, name="login"),
    url('^logout/$', logout, name="logout"),
    url('^register/$', register, name="register"),
    url('^confirm/(?P<confirm_code>.+)/$', confirm_email, name="confirm-email"),
    url('^$', dashboard, name="dashboard"),
]
