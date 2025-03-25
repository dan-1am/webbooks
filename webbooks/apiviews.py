from rest_framework import viewsets

import webbooks.models as m
import webbooks.serializers as s



class AuthorViewSet(viewsets.ModelViewSet):
    queryset = m.Author.objects.all()
    serializer_class = s.AuthorSerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = m.Genre.objects.all()
    serializer_class = s.GenreSerializer

class SequenceViewSet(viewsets.ModelViewSet):
    queryset = m.Sequence.objects.all()
    serializer_class = s.SequenceSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = m.Book.objects.all()
    serializer_class = s.BookSerializer


