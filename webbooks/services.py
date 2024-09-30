import hashlib
from pathlib import Path

from .fb2book import FB2Book
from . import conf
from .models import *


def file_hash(file):
    is_file_like = all(hasattr(file, attr)
        for attr in ('seek', 'close', 'read', 'write'))
    if not is_file_like:
        file = open(file, "rb")
    hasher = hashlib.file_digest(file, "md5")
    return hasher.hexdigest()


def get_book_path(full_path):
    return Path(full_path).relative_to(conf.WEBBOOKS_ROOT)


def find_by_path(book_path, values=None):
    query = Book.objects.filter(file=book_path)
    if values:
        query = query.values(*values)
    records = list( query[:1] )
    if records:
        return records[0]


def set_authors(book, names):
    names = sorted(names) if names else ["Unknown"]
    authors = [Author.objects.get_or_create(name=n)[0] for n in names]
    book.authors.set(authors)


def set_genres(book, genres):
    genres = [Genre.objects.get_or_create(name=n)[0] for n in genres]
    book.genres.set(genres)


def set_sequence(book, name):
    if name:
        book.sequence = Sequence.objects.get_or_create(name=name)[0]
    else:
        book.sequence = None


def fill_extra_info(book, fb2):
    for field in ('date','annotation', 'sequence_number'):
        setattr(book, field, getattr(fb2, field, ""))
    set_sequence(book, fb2.sequence)
    book.save()
    set_authors(book, fb2.authors)
    set_genres(book, fb2.genres)


def add_book(full_path, hash=None, id=None):
    fb2 = FB2Book(file=full_path)
    fb2.describe()
    if hash is None:
        hash = file_hash(full_path)
    book_path = get_book_path(full_path)
    book = Book(title=fb2.title, file=book_path, hash=hash)
    if id is not None:
        book.id = id
    fill_extra_info(book, fb2)
    return book


def inspect_book(full_path):
    hash = file_hash(full_path)
    book_path = get_book_path(full_path)
    found_book = find_by_path(book_path)
    if found_book and found_book.hash == hash:
        return found_book, ""
    id = found_book.id if found_book else None
    book = add_book(full_path, hash, id=id)
    action = "update" if found_book else "create"
    return book, action
