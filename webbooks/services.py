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


def get_default_path(book_path):
    return Path(conf.WEBBOOKS_ROOT, Path(book_path).name)


def get_book_path(full_path):
    return Path(full_path).relative_to(conf.WEBBOOKS_ROOT)


def find_by_path(book_path, values=None):
    query = Book.objects.filter(file=book_path)
    if values:
        query = query.values(*values)
    records = list( query[:1] )
    if records:
        return records[0]


def find_by_hash(book_hash, values=None):
    query = Book.objects.filter(hash=book_hash)
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


def check_book_file(full_path):
    """ Check and update if file in the library is changed. """
    hash = file_hash(full_path)
    book_path = get_book_path(full_path)
    found_book = find_by_path(book_path)
    if found_book:
        if found_book.hash == hash:
            return found_book, "exists"
        # todo: Use old info as default. Maybe discard new info?
        book = add_book(full_path, hash, id=found_book.id)
        return book, "updated"
    found_book = find_by_hash(hash)
    if found_book:
        if not found_book.full_path().is_file():
            found_book.file = book_path
            found_book.save()
            return found_book, "moved"
    book = add_book(full_path, hash)
    return book, "created"


def add_book_file(full_path):
    """ Add uploaded file to library. """
    hash = file_hash(full_path)
    found_book = find_by_hash(hash)
    if found_book:
        return found_book, "exists"
    new_path = get_default_path(full_path)
    book_path = get_book_path(new_path)
    found_book = find_by_path(book_path)
    if found_book:
        # todo: special page "exists but different", cancel/replace
        return found_book, "exists"
    Path(full_path).replace(new_path)
    book = add_book(new_path, hash)
    return book, "created"
