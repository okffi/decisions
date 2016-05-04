from django.shortcuts import render, get_object_or_404

from decisions.news.models import Entry


def entry(request, year, object_id, slug):
    e = get_object_or_404(Entry, pub_date__year=year, pk=object_id, slug=slug)

    return render(request, "news/entry.html", {"entry": e})
