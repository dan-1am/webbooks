from django.db import models
from rest_framework import serializers

from webbooks.models import Genre,Author,Sequence,Book,Comment


def view_name(cls):
    app_label = cls._meta.app_label
    model_name = cls._meta.model_name
    return f"{app_label}:{model_name}-detail"


def linked_id_field(cls):
    return serializers.HyperlinkedIdentityField(view_name=view_name(cls))


def linked_related_field(cls, many=False):
    return serializers.HyperlinkedRelatedField(
        many=many,
        view_name=view_name(cls),
        queryset=cls.objects.all()
    )


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    url = linked_id_field(Author)
    class Meta:
        model = Author
        fields = ['url', 'id', 'name']


class GenreSerializer(serializers.HyperlinkedModelSerializer):
    url = linked_id_field(Genre)
    class Meta:
        model = Genre
        fields = ['url', 'id', 'name']


class SequenceSerializer(serializers.HyperlinkedModelSerializer):
    url = linked_id_field(Sequence)
    class Meta:
        model = Sequence
        fields = ['url', 'id', 'name']


class BookSerializer(serializers.HyperlinkedModelSerializer):
    url = linked_id_field(Book)
    authors = linked_related_field(Author, True)
    genres = linked_related_field(Genre, True)
    sequence = linked_related_field(Sequence)
    class Meta:
        model = Book
        fields = ['url', 'id', 'title', 'authors', 'genres', 'date',
            'annotation', 'sequence', 'sequence_number', 'file', 'hash']


class FullBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'genres', 'date',
            'annotation', 'sequence', 'sequence_number', 'file', 'hash']
        depth = 1
