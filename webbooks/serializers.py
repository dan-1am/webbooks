from django.db import models
from rest_framework import serializers

from webbooks.models import Genre,Author,Sequence,Book,Comment


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name']


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'authors']

"""    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, blank=True)
    date = models.CharField(max_length=10, blank=True)
    annotation = models.TextField(blank=True)
    sequence = models.ForeignKey(Sequence, blank=True, null=True, on_delete=models.CASCADE)
    sequence_number = models.IntegerField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, blank=True)
    file = models.CharField(max_length=512)
    hash = models.CharField(max_length=32)
"""
