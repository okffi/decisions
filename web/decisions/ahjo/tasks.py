from datetime import timedelta

from django.core.management import call_command
from django.utils.timezone import now

from decisions.celery import app
from decisions.ahjo import fetch as ahjo_fetch
from decisions.subscriptions.process import process_subscriptions
from decisions.ahjo.models import AgendaItem


@app.task()
def fetch_index():
    # Fetch all sorts of new data
    # Fetchers should give a date after which all new entries are
    # We will always re-index at least two hours (this is supposed to be run every hour)
    earliest_dates = [now() - timedelta(hours=2)]

    if AgendaItem.objects.count():
        earliest_dates.append(AgendaItem.objects.latest().last_modified_time)
    ahjo_fetch.import_latest()

    # Reindex Haystack
    call_command("update_index", interactive=False, after=min(earliest_dates).isoformat())

@app.task()
def process():
    # Send mail about saved searches
    process_subscriptions()
