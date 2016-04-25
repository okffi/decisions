import itertools

from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.http import JsonResponse, Http404

from decisions.ahjo.utils import b36decode
from decisions.ahjo.models import AgendaItem


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
            "id_b36": ahjo_id_b36,
        }
    )


def get_geometry(request, agendaitem_id):
    item = get_object_or_404(AgendaItem, pk=agendaitem_id)

    return JsonResponse({"content": item.original["issue"]["geometries"]})
