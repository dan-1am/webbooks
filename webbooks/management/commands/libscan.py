from pathlib import Path
import time
from django.core.management.base import BaseCommand, CommandError

import webbooks.conf
from webbooks.models import *
from webbooks.services import check_book_file



#raise CommandError('Poll "%s" does not exist' % poll_id)


def recurse_path(path):
    for file in path.iterdir():
        if file.is_dir():
            yield from recurse_path(file)
        else:
            yield file


def scan_lib_dir(output):
    for file in recurse_path( Path(conf.WEBBOOKS_ROOT) ):
        if file.is_relative_to(conf.WEBBOOKS_UPLOAD):
            continue
        try:
            if file.name.endswith((".fb2", ".fb2.zip")):
                book, status = check_book_file(file)
        except:
            output.write(f"error: {file}")
            raise
        else:
            if status != "exists":
                output.write(f"{status}: {file}")


def clear_missing(output):
    for book in Book.objects.all():
        if not book.full_path().exists():
            output.write(f"Deleting {book.file}")
            book.delete()


def stopwatch(start=None):
    now = time.perf_counter()
    if start is None:
        return now
    print(f"Elapsed {now-start:.2}s")
    return now


class Command(BaseCommand):
    help = "Scans filesystem for new books"

    def handle(self, *args, **options):
        start = stopwatch()
        self.stdout.write(f"Clear missing books")
        clear_missing(self.stdout)
        self.stdout.write(f"Searching new books in {conf.WEBBOOKS_ROOT}")
        scan_lib_dir(self.stdout)
        stopwatch(start)
