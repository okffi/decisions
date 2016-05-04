from django import template
from django.utils.translation import get_language
from django.utils.timezone import now

register = template.Library()

from decisions.news.models import Entry


@register.inclusion_tag("news/ticker.html")
def news_ticker():
    return {
        "entries": Entry.objects.filter(pub_date__lte=now(), language=get_language())[:5]
    }
