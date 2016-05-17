from haystack import indexes

from decisions.ahjo.models import AgendaItem


class AgendaItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr="last_modified_time")
    subject = indexes.CharField(model_attr="subject")

    def get_model(self):
        return AgendaItem

    def get_updated_field(self):
        return "last_modified_time"
