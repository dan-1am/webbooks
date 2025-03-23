import json

from django.test import TestCase
from django.urls import reverse

from webbooks.models import Book



class WebbooksAPITest(TestCase):

    book_list_url = reverse("webbooks:api_book_list")

    def create_books(self, count):
        return [
            Book.objects.create(title="Book "+str(id))
            for id in range(count)
        ]

    def test_get_returns_json200(self):
        book1 = self.create_books(1)[0]
        response = self.client.get(self.book_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")

    def test_get_returns_all_books(self):
        created = self.create_books(2)
        response = self.client.get(self.book_list_url)
        data_list = json.loads( response.content.decode("utf8") )
        data_dict = {item['id']: item for item in data_list}
        for book in created:
            self.assertEqual(book.title, data_dict[book.id]['title'])
