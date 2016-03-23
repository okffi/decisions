from django.conf.urls import url

from haystack.generic_views import SearchView
from haystack.forms import SearchForm

from decisions.subscriptions.voikko import VoikkoSearchQuerySet


class DecisionsSearchForm(SearchForm):
    def __init__(self, *args, **kwargs):
        kwargs["searchqueryset"] = VoikkoSearchQuerySet()
        super(DecisionsSearchForm, self).__init__(*args, **kwargs)

class DecisionsSearchView(SearchView):
    form_class = DecisionsSearchForm

urlpatterns = [
    url('^$', DecisionsSearchView.as_view(), name="haystack_search"),
]
