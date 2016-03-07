from django.core.management.base import BaseCommand, CommandError

from decisions.subscriptions import process


class Command(BaseCommand):
    def handle(self, *args, **options):
        results = process.process_subscriptions()
        self.stdout.write(self.style.SUCCESS("Processed %d new hits" % results))
