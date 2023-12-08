from django.core.management.base import BaseCommand, CommandError

from library.models import *


class Command(BaseCommand):
    help = "Clear library db"

    def handle(self, *args, **options):
        self.stdout.write(f"Clearing library db...")
        Book.objects.all().delete()
        Sequence.objects.all().delete()
        Author.objects.all().delete()
        Genre.objects.all().delete()
