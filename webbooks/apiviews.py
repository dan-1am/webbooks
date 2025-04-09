from rest_framework import viewsets

import webbooks.models as m
import webbooks.serializers as s



class AuthorViewSet(viewsets.ModelViewSet):
    queryset = m.Author.objects.order_by("id")
    serializer_class = s.AuthorSerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = m.Genre.objects.order_by("id")
    serializer_class = s.GenreSerializer

class SequenceViewSet(viewsets.ModelViewSet):
    queryset = m.Sequence.objects.order_by("id")
    serializer_class = s.SequenceSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = m.Book.objects.order_by("id")
    serializer_class = s.BookSerializer

class FullBookViewSet(viewsets.ModelViewSet):
    queryset = m.Book.objects.order_by("id").prefetch_related()
    serializer_class = s.FullBookSerializer
