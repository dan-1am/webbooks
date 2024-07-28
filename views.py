from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from django.db.models import Count,OuterRef,Subquery
from django.db.models.functions import Coalesce

from .models import *
from .fb2book import FB2Book


#def index(request):
#    return HttpResponse('Library index...')

def index(request):
    return render(request, "webbooks/index.html", {})



class IndexView(generic.ListView):

    def get_queryset(self):
        return Author.objects.annotate(book_count=Count("book")).order_by("name")


def group_by(sequence, getkey):
    groups = {}
    for item in sequence:
        key = getkey(item)
        if key in groups:
            groups[key].append(item)
        else:
            groups[key] = [item]
    return groups


def by_sequence(books):
    groups = group_by(books, lambda b: b.sequence and b.sequence.name)
    ungrouped = groups.pop(None, None)
    for group in groups.values():
        group.sort(key=lambda b: b.sequence_number or 0)
    groups = [(seq, groups[seq]) for seq in sorted(groups)]
    if ungrouped:
        groups.insert(0, ("No sequence", ungrouped))
    return groups


class AuthorView(generic.DetailView):
    model = Author
    template_name = "webbooks/author.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.object
        books = author.book_set.select_related("sequence").all()
        context['book_count'] = len(books)
        context['grouped_books'] = by_sequence(books)
        return context


def book_authors(book):
    # This gives wrong book_count:
    #authors = book.authors.all().annotate(book_count=Count("book"))
    ids = book.authors.values("id")
    authors = Author.objects.filter(id__in=ids).annotate(book_count=Count("book"))
    return authors


class BookView(generic.DetailView):
    model = Book
    template_name = "webbooks/book.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.object
        context['authors'] = book_authors(book)
        return context


class ReadView(generic.DetailView):
    model = Book
    template_name = "webbooks/read.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.object
        context['authors'] = book_authors(book)
        fb2 = FB2Book(file=book.file)
        html = fb2.to_html()
        context['text'] = fb2.get_toc() + html
        return context


def find_field_dupes(field):
    dupes = Book.objects.values(field).annotate(field_count=Count(field)) \
        .order_by().filter(field_count__gt=1)
    return [o[field] for o in dupes]

class DuplicatesView(generic.ListView):
    template_name = "webbooks/book_list.html"
    context_object_name = "book_list"

    def get_queryset(self):
        hashes = find_field_dupes("hash")
        return Book.objects.filter(hash__in=hashes).order_by("hash")
