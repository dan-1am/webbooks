from django.db import models
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name



class Author(models.Model):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name



class Sequence(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name



class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, blank=True)
    date = models.CharField(max_length=10, blank=True)
    annotation = models.TextField(blank=True)
    sequence = models.ForeignKey(Sequence, blank=True, null=True, on_delete=models.CASCADE)
    sequence_number = models.IntegerField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, blank=True)
    file = models.CharField(max_length=512)
    hash = models.CharField(max_length=32)

    def __str__(self):
        return self.title



class Comment(models.Model):
    text = models.TextField()
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, blank=True)
    userid = models.IntegerField(blank=True, null=True)
    time = models.DateTimeField(default=timezone.now)

    def anchor(self):
        return f"cmt{self.pk}"

    def __str__(self):
        return self.text
