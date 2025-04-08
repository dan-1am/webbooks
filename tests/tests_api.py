import json

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from webbooks.models import Book


def remove_paginator(data):
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    return data


class WebbooksAPITest(TestCase):

    book_list_url = reverse("webbooks:book-list")

    def create_books(self, count):
        return [
            Book.objects.create(title="Book "+str(id))
            for id in range(count)
        ]

    def test_reverse_drf_router_view(self):
        try:
            bookurl = reverse("webbooks:book-detail", args=[1])
        except:
            self.fail()

    def test_get_returns_json200(self):
        book1 = self.create_books(1)[0]
        response = self.client.get(self.book_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")

    def test_get_returns_all_books(self):
        created = self.create_books(2)
        response = self.client.get(self.book_list_url)
        data_list = json.loads( response.content.decode("utf8") )
        data_list = remove_paginator(data_list)
        data_dict = {item["id"]: item for item in data_list}
        for book in created:
            self.assertEqual(book.title, data_dict[book.id]["title"])

    def action_create(self, url, data):
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def action_read(self, url, data):
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        received = remove_paginator(response.data)
        if isinstance(data, dict):
            for k in data:
                self.assertEqual(data[k], received[k])
        else:
            for a,b in zip(data, received):
                for k in a:
                    self.assertEqual(a[k], b[k])

    def view_actions(self, model, data):
        response = self.action_create(reverse(f"webbooks:{model}-list"), data)
        pk = response.data["id"]
        self.action_read(reverse(f"webbooks:{model}-list"), [data])
        self.action_read(reverse(f"webbooks:{model}-detail", args=[pk]), data)

    def test_author_views(self):
        data = {"name": "Author 1"}
        self.view_actions("author", data)

    def test_genre_views(self):
        data = {"name": "genre 1"}
        self.view_actions("genre", data)

    def test_sequence_views(self):
        data = {"name": "sequence 1"}
        self.view_actions("sequence", data)

    def test_book_views(self):
        data = {"title": "book 1", "file": "file1", "hash": "abcd"}
        self.view_actions("book", data)
