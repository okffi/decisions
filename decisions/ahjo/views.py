import itertools

from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.http import JsonResponse, HttpResponseBadRequest

from decisions.ahjo.utils import b36decode
from decisions.ahjo.models import AgendaItem
from decisions.ahjo.forms import CommentForm


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

    return render(
        request,
        "ahjo/view.html",
        {
            "agendaitem": item,
            "comment_form": CommentForm(),
            "id_b36": ahjo_id_b36,
        }
    )

class JsonResponseBadRequest(JsonResponse, HttpResponseBadRequest):
    pass

def comment(request, ahjo_id_b36):
    ahjo_id = b36decode(ahjo_id_b36)
    item = get_object_or_404(AgendaItem, ahjo_id=ahjo_id)
    if request.method != "POST":
        return JsonResponseBadRequest(
            {"errors": {"general": "POST only, not GET"}}
        )

    form = CommentForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.agendaitem = item
        obj.save()
        return JsonResponse({"content": "success"})
    else:
        return JsonResponseBadRequest({"errors": form.errors})

def get_comments(request, ahjo_id_b36):
    ahjo_id = b36decode(ahjo_id_b36)
    item = get_object_or_404(AgendaItem, ahjo_id=ahjo_id)

    comments = itertools.groupby(
        (c.get_dict() for c
         in item.comment_set.order_by('selector', 'created')),
        lambda c: c["selector"]
    )

    comments = dict((k, list(v)) for k,v in comments)

    return JsonResponse({
        "content": comments,
    })
