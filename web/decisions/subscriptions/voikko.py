from django.utils.translation import get_language

from haystack.query import SearchQuerySet

from decisions.subscriptions.templatetags.voikko_tags import voikko_simplify


class VoikkoSearchQuerySet(SearchQuerySet):
    def auto_query(self, query_string, **kwargs):
        lang = get_language()
        if lang == u"fi":
            query_string = voikko_simplify(query_string, "fi")

        return super(VoikkoSearchQuerySet, self).auto_query(
            query_string,
            **kwargs
        )
