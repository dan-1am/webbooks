from django.test import TestCase

from .models import *



class TestWebbooks(TestCase):
    databases = "__all__"

    def setUp(self):
        Book.objects.create(title="Title1", file="file1.fb2", hash="hash1")
        Book.objects.create(title="Title2", file="file2.fb2", hash="hash2")

    def test1(self):
        book = Book.objects.get(title__contains="2")
        self.assertEqual(book.title, "Title2")
