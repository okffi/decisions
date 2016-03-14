"""decisions URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.i18n import javascript_catalog
from django.shortcuts import render

from decisions.subscriptions.forms import LoginForm, RegisterForm

js_info_dict = {
    'packages': ('decisions',),
}

def index(request):
    return render(request, "index.html", {
        "login_form": LoginForm(),
        "register_form": RegisterForm(),
    })

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^ahjo/', include('decisions.ahjo.urls')),
    url(r'^jsi18n/$',
        javascript_catalog,
        js_info_dict,
        name='javascript-catalog'),
    url(r'^search/', include('decisions.subscriptions.search_urls')),
    #url(r'^search/', include('haystack.urls')),
    url(r'^$', index, name='index'),
    url(r'^subscriptions/', include('decisions.subscriptions.urls')),
]
