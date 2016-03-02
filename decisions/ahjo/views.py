from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify

from decisions.ahjo.utils import b36decode
from decisions.ahjo.models import AgendaItem

# Create your views here.

def search(request):
    "Simple search and search results view"
    q = request.GET.get("q")

    if q:
        results = AgendaItem.objects.textsearch(q)
    else:
        results = []

    return render(request, "ahjo/search.html", {"results": results, "q": q})

def view(request, ahjo_id_b36, slug=None):
    ahjo_id = b36decode(ahjo_id_b36)
    item = get_object_or_404(AgendaItem, ahjo_id=ahjo_id)
    if slug != slugify(item.subject):
        return redirect(
            'ahjo-view',
            ahjo_id_b36=ahjo_id_b36,
            slug=slugify(item.subject)
        )

    return render(request, "ahjo/view.html", {"agendaitem": item})
