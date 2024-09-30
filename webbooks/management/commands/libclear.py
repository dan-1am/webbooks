from django.core.management.base import BaseCommand, CommandError

from webbooks.models import *


class Command(BaseCommand):
    help = "Clear webbooks db"

    def handle(self, *args, **options):
        self.stdout.write(f"Clearing webbooks db...")
        Book.objects.all().delete()
        Sequence.objects.all().delete()
        Author.objects.all().delete()
        Genre.objects.all().delete()
