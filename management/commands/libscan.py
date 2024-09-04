from hashlib import md5
from pathlib import Path
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from webbooks.models import *
from webbooks.fb2book import FB2Book


#    try:
#        poll = Poll.objects.get(pk=poll_id)
#    except Poll.DoesNotExist:
#        raise CommandError('Poll "%s" does not exist' % poll_id)


def recurse_path(path):
    for file in path.iterdir():
        if file.is_dir():
            yield from recurse_path(file)
        else:
            yield file


def scanfb2(full_path, output):
    book_path = Path(full_path).relative_to(settings.LIBRARY_DIR)
    records = list( Book.objects.filter(file=book_path) )
    filehash = md5( full_path.read_bytes() ).hexdigest()
    if records and records[0].hash == filehash:
        output.write(f"Exists: {book_path}")
        return
    fb2 = FB2Book(file=full_path)
    fb2.describe()
    if fb2.authors:
        asort = sorted(fb2.authors)
    else:
        asort = ["Unknown"]
    authors = [Author.objects.get_or_create(name=n)[0] for n in asort]
    fields = ('date','annotation')
    data = {f: getattr(fb2, f, "") for f in fields}
    data['file'] = book_path;
    data['hash'] = filehash;
    if fb2.sequence:
        data['sequence'] = Sequence.objects.get_or_create(name=fb2.sequence)[0]
    else:
        data['sequence'] = None
    data['sequence_number'] = fb2.sequence_number
    if not records:
        book = Book.objects.create(title=fb2.title, **data)
        output.write(f"Added: {fb2.title}")
    else:
        book = records[0]
        output.write(f"Exists: {fb2.title}")
        for k,v in data:
            setattr(book, k, v)
    if fb2.genres:
        genres = [Genre.objects.get_or_create(name=n)[0] for n in fb2.genres]
        book.genres.set(genres)
    book.authors.set(authors)


def scan_lib_dir(output):
    for file in recurse_path( Path(settings.LIBRARY_DIR) ):
        output.write(f"File: {file}")
        if file.name.endswith((".fb2", ".fb2.zip")):
            scanfb2(file, output)


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
        self.stdout.write(f"Searching new books in {settings.LIBRARY_DIR}")
        scan_lib_dir(self.stdout)
        self.stdout.write(f"Clear missing books")
        clear_missing(self.stdout)
        stopwatch(start)
