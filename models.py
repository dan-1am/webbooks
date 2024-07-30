from django.db import models



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
