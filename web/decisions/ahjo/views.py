import itertools

from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.http import JsonResponse, HttpResponseBadRequest, Http404

from decisions.ahjo.utils import b36decode
from decisions.ahjo.models import AgendaItem
from decisions.ahjo.forms import CommentForm
from decisions.comments.models import Comment


def view(request, ahjo_id_b36, slug=None, disambiguation_id=None):
    ahjo_id = b36decode(ahjo_id_b36)

    items = AgendaItem.objects.filter(ahjo_id=ahjo_id)

    if not items:
        raise http.Http404

    if disambiguation_id:
        item = get_object_or_404(AgendaItem, pk=disambiguation_id)
    else:
        item = items.earliest()

    more_items = len(items) > 1

    if more_items and not disambiguation_id:
        # keep URLs stable
        return redirect(
            'ahjo-view',
            ahjo_id_b36=ahjo_id_b36,
            slug=slugify(item.subject),
            disambiguation_id=item.pk
        )


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
            "more_items": more_items,
            "items": items,
            "comment_form": CommentForm(),
            "id_b36": ahjo_id_b36,
        }
    )

class JsonResponseBadRequest(JsonResponse, HttpResponseBadRequest):
    pass

def comment(request, ahjo_id_b36, disambiguation_id):
    if request.user.is_anonymous():
        return JsonResponseBadRequest(
            {"errors": {"general": "must be logged in"}}
        )
    ahjo_id = b36decode(ahjo_id_b36)
    item = get_object_or_404(AgendaItem, ahjo_id=ahjo_id, pk=disambiguation_id)
    if request.method != "POST":
        return JsonResponseBadRequest(
            {"errors": {"general": "POST only, not GET"}}
        )

    form = CommentForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.agendaitem = item
        obj.user = request.user
        obj.save()
        return JsonResponse({"content": "success"})
    else:
        return JsonResponseBadRequest({"errors": form.errors})

def get_comments(request, ahjo_id_b36, disambiguation_id):
    ahjo_id = b36decode(ahjo_id_b36)
    item = get_object_or_404(AgendaItem, ahjo_id=ahjo_id, pk=disambiguation_id)

    comment_set = Comment.objects.filter(object_id=item.pk, content_type=ContentType.get_for_model(AgendaItem))

    comments = itertools.groupby(
        (c.get_dict() for c
         in comment_set.order_by('selector', 'created')),
        lambda c: c["selector"]
    )

    comments = dict((k, list(v)) for k,v in comments)

    return JsonResponse({
        "content": comments,
    })

def get_geometry(request, agendaitem_id):
    item = get_object_or_404(AgendaItem, pk=agendaitem_id)

    return JsonResponse({"content": item.original["issue"]["geometries"]})
