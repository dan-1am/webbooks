from pathlib import Path
from hashlib import md5
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from library.models import *
from library.fb2book import FB2Book


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


def scanfb2(file, output):
    records = list( Book.objects.filter(file=file) )
    filehash = md5( file.read_bytes() ).hexdigest()
    if records and records[0].hash == filehash:
        output.write(f"Exists: {file}")
        return
    fb2 = FB2Book(file=file)
    fb2.describe()
    if fb2.authors:
        asort = sorted(fb2.authors)
    else:
        asort = ["Unknown"]
    authors = [Author.objects.get_or_create(name=n)[0] for n in asort]
    fields = ('date','annotation')
    data = {f: getattr(fb2, f, None) or "" for f in fields }
    data['file'] = file;
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


#!!!todo
def scanfb2zip(file):
    pass


def scan_lib_dir(output):
    for file in recurse_path( Path(settings.LIBRARY_DIR) ):
        output.write(f"File: {file}")
        if file.name.endswith(".fb2.zip"):
            scanfb2zip(file)
        elif file.name.endswith(".fb2"):
            scanfb2(file, output)


def clear_missing(output):
    for book in Book.objects.values("pk", "file"):
        if not Path(book["file"]).exists():
            output.write(f"Deleting {book['file']}")
            Book.objects.filter(pk=book["pk"]).delete()


class Command(BaseCommand):
    help = "Scans filesystem for new books"

    def handle(self, *args, **options):
        self.stdout.write(f"Searching new books in {settings.LIBRARY_DIR}")
        scan_lib_dir(self.stdout)
        self.stdout.write(f"Clear missing books")
        clear_missing(self.stdout)
