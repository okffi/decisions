from django.conf.urls import url

from decisions.subscriptions.profile import (
    login,
    logout,
    register,
    login_or_register,
    confirm_email,
    profile,
    edit_profile,

    change_password,
    forgot_password,
    reset_password
)


urlpatterns = [
    url(r'^$', edit_profile, name='edit-profile'),
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, name="logout"),
    url(r'^register/$', register, name="register"),
    url(r'^login-or-register/$', login_or_register, name="login-or-register"),
    url(r'^confirm/(?P<confirm_code>.+)/$', confirm_email, name="confirm-email"),
    url(r'^change-password/$', change_password, name="change-password"),
    url(r'^forgot-password/$', forgot_password, name="forgot-password"),
    url(r'^reset-password/(?P<reset_code>.+)/$', reset_password, name="reset-password")
]
