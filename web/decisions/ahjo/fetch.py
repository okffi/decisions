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
            "last_modified_time__gt": since,
            "order_by": "-last_modified_time",
            "limit": limit,
        })

    response.raise_for_status()
    return response.json()

def import_latest():
    if AgendaItem.objects.count():
        new = get_decisions_since(AgendaItem.objects.latest().last_modified_time)
    else:
        new = get_decisions_since()

    for obj in new["objects"]:
        AgendaItem.objects.create_from_json(obj)

    return len(new["objects"])
