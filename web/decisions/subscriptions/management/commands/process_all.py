from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from decisions.subscriptions import process


class Command(BaseCommand):
    def handle(self, *args, **options):
        # fetch sources
        call_command("ahjo_fetch")
        # .. more sources ..

        # update search
        call_command("update_index")

        # process subscriptions
        call_command("process_subscriptions")
