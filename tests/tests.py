from pathlib import Path
import tempfile
from django.test import TestCase

from webbooks import conf
from webbooks.fb2book import FB2Book
from webbooks.models import *
from webbooks.services import *


def temp_file(content, mode="w+b"):
    file = tempfile.SpooledTemporaryFile(mode="w+b")
    file.write(content)
    file.seek(0)
    return file


class TestServices(TestCase):
    databases = "__all__"

    def setUp(self):
        if Book.objects.count() == 0:
            Book.objects.create(title="Title1", file="file1.fb2", hash="hash1")
            Book.objects.create(title="Title2", file="file2.fb2", hash="hash2")

    def test_file_hash(self):
        file = temp_file(b"tempdata")
        hash = file_hash(file)
        self.assertEqual(hash, "c1123658d9771a13cd4570a0dc6965fe")

    def test_get_book_path(self):
        full_path = Path(conf.WEBBOOKS_ROOT, "subdir", "book.fb2")
        book_path = get_book_path(full_path)
        self.assertEqual(book_path, Path("subdir", "book.fb2"))

    def test_find_by_path(self):
        book1 = find_by_path("file1.fb2", values=["id", "hash"])
        self.assertEqual(book1["id"], 1)
        book2 = find_by_path("file2.fb2")
        self.assertEqual(book2.id, 2)

    def test_set_authors(self):
        all_authors = [("a", "b", "c"), ("f", "g", "h")]
        books = Book.objects.all()[:2]
        for book,authors in zip(books, all_authors):
            set_authors(book, authors)
        for book,authors in zip(books, all_authors):
            found = Book.objects.get(authors__name=authors[1])
            self.assertEqual(book.file, found.file)
            authors2 = sorted( found.authors.values_list("name", flat=True) )
            self.assertEqual(authors2, list(authors))

    def test_set_genres(self):
        all_genres = [("a", "b", "c"), ("f", "g", "h")]
        books = Book.objects.all()[:2]
        for book,genres in zip(books, all_genres):
            set_genres(book, genres)
        for book,genres in zip(books, all_genres):
            found = Book.objects.get(genres__name=genres[1])
            self.assertEqual(book.file, found.file)
            genres2 = sorted( found.genres.values_list("name", flat=True) )
            self.assertEqual(genres2, list(genres))

    def test_set_sequence(self):
        book = Book.objects.all()[0]
        set_sequence(book, "seq1")
        self.assertEqual(book.sequence.name, "seq1")
        set_sequence(book, "")
        self.assertEqual(book.sequence, None)

    fb2_example = b"""\
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
<description>
<title-info>
    <genre>prose_classic</genre>
    <author>
      <first-name>Bob</first-name>
      <middle-name>Jr</middle-name>
      <last-name>Doe</last-name>
      <nickname>Tester</nickname>
    </author>
    <book-title>Title</book-title>
    <annotation>
      <p>Annotation.</p>
    </annotation>
    <date>2001</date>
    <sequence name="Sequence." number="2"/>
    <coverpage><image l:href="#cover.jpg"/></coverpage>
</title-info>
</description>
<body></body>
</FictionBook>
"""

    def test_fill_extra_info(self):
        fb2 = FB2Book(self.fb2_example)
        fb2.describe()
        book = Book(title=fb2.title, file="1.fb2", hash="123")
        fill_extra_info(book, fb2)
        for field in ("date","annotation","sequence_number"):
            self.assertEqual(getattr(book, field), getattr(fb2, field))
        self.assertEqual(book.sequence.name, fb2.sequence)
        authors = sorted( book.authors.values_list("name", flat=True) )
        self.assertEqual(authors, fb2.authors)
        genres = sorted( book.genres.values_list("name", flat=True) )
        self.assertEqual(genres, fb2.genres)

    def find_some_book(self):
        return next( Path(conf.WEBBOOKS_ROOT).glob("**/*.fb2*") )

    def test_add_book(self):
        full_path = self.find_some_book()
        book = add_book(full_path)
        book_path = get_book_path(full_path)
        self.assertEqual(book.file, book_path)

    def test_check_book_file(self):
        full_path = self.find_some_book()
        book, status = check_book_file(full_path)
        with self.subTest(key="create"):
            self.assertEqual(status, "created")
            book_path = get_book_path(full_path)
            book_count = Book.objects.filter(file=book_path).count()
            self.assertEqual(book_count, 1)
        with self.subTest(key="update"):
            Book.objects.filter(id=book.id).update(hash="123")
            _, status = check_book_file(full_path)
            self.assertEqual(status, "updated")
            hash = Book.objects.values_list("hash", flat=True).get(id=book.id)
            self.assertNotEqual(hash, "123")

    def test_add_book_file(self):
        full_path = self.find_some_book()
        book, status = add_book_file(full_path)
        with self.subTest(key="create"):
            self.assertEqual(status, "created")
            book_path = get_book_path(full_path)
            book_count = Book.objects.filter(file=book_path).count()
            self.assertEqual(book_count, 1)
        with self.subTest(key="update"):
            Book.objects.filter(id=book.id).update(hash="123")
            _, status = add_book_file(full_path)
            self.assertEqual(status, "exists")
