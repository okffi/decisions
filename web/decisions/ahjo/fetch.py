from datetime import timedelta

from django.utils.timezone import now

import requests

from decisions.ahjo.models import AgendaItem


def get_decisions_since(since=None, limit=50):
    if since is None:
        since = now() - timedelta(days=2)

    url = "http://dev.hel.fi/paatokset/v1/agenda_item/"

    response = requests.get(
        url,
        params={
            "last_modified_time__gt": since.isoformat(),
            "order_by": "last_modified_time",
            "limit": limit,
        })

    response.raise_for_status()
    return response.json()

def get_decisions_before(before, limit=100):
    response = requests.get(url, {
        "last_modified_time__lt": before.isoformat(),
        "order_by": "-last_modified_time",
        "limit": limit
    })
    response.raise_for_status()
    objects = response.json()["objects"]
    for object in objects:
        if AgendaItem.objects.filter(ahjo_id=object["id"]).count(): continue
        before = AgendaItem.objects.create_from_json(object).last_modified_time
    return before

def import_latest():
    if AgendaItem.objects.count():
        new = get_decisions_since(AgendaItem.objects.latest().last_modified_time)
    else:
        new = get_decisions_since()

    for obj in new["objects"]:
        AgendaItem.objects.create_from_json(obj)

    return len(new["objects"])
