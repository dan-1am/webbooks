from django.db import models
from rest_framework import serializers

from webbooks.models import Genre,Author,Sequence,Book,Comment



class ScopedSerializer(serializers.HyperlinkedModelSerializer):
    """Add "app_name:" scope to view name for related fields."""
    def build_field(self, *args, **kwargs):
        field_class,field_kwargs = super().build_field(*args, **kwargs)
        if 'view_name' in field_kwargs:
            app_name = self.Meta.model._meta.app_label
            field_kwargs['view_name'] = f"{app_name}:{field_kwargs['view_name']}"
        return field_class, field_kwargs


class AuthorSerializer(ScopedSerializer):
    class Meta:
        model = Author
        fields = ['url', 'id', 'name']


class GenreSerializer(ScopedSerializer):
    class Meta:
        model = Genre
        fields = ['url', 'id', 'name']


class SequenceSerializer(ScopedSerializer):
    class Meta:
        model = Sequence
        fields = ['url', 'id', 'name']


class BookSerializer(ScopedSerializer):
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
