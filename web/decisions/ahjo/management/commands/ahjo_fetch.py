from django.core.management.base import BaseCommand, CommandError

from decisions.ahjo import fetch


class Command(BaseCommand):
    def handle(self, *args, **options):
        results = fetch.import_latest()
        self.stdout.write(self.style.SUCCESS("Fetched %d new items" % results))
