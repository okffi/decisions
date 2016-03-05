from haystack import indexes

from decisions.ahjo.models import AgendaItem


class AgendaItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return AgendaItem
