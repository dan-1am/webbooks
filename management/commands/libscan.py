from pathlib import Path
from hashlib import md5
from django.core.management.base import BaseCommand, CommandError

from library.settings import libdir
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


def scanfb2(file):
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
    data['hash'] = md5( file.read_bytes() ).hexdigest()
    if fb2.sequence:
        data['sequence'] = Sequence.objects.get_or_create(name=fb2.sequence)[0]
    else:
        data['sequence'] = None
    data['sequence_number'] = fb2.sequence_number
    n = Book.objects.filter(file=file).count()
    if not n:
        book = Book.objects.create(title=fb2.title, **data)
        book.authors.set(authors)
        if fb2.genres:
            genres = [Genre.objects.get_or_create(name=n)[0] for n in fb2.genres]
            book.genres.set(genres)
        print(f"Added: {fb2.title}")
    else:
        print(f"Exists: {fb2.title}")

#!!!todo
def scanfb2zip(file):
    pass



class Command(BaseCommand):
    help = "Scans filesystem for new books"

    def handle(self, *args, **options):
        self.stdout.write(f"Scanning library dir {libdir}")
        for file in recurse_path( Path(libdir) ):
            print(f"File: {file}")
            if file.name.endswith(".fb2.zip"):
                scanfb2zip(file)
            elif file.name.endswith(".fb2"):
                scanfb2(file)
