from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.views.decorators.http import require_POST
from django.db.models import Count,OuterRef,Subquery
from django.db.models.functions import Coalesce

from . import conf
from .fb2book import FB2Book
from .models import *
from .services import inspect_book


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
        context['comments'] = Comment.objects.filter(book=book)
        return context


class ReadView(generic.DetailView):
    model = Book
    template_name = "webbooks/read.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.object
        context['authors'] = book_authors(book)
        fb2 = FB2Book(file=book.full_path())
        html = fb2.to_html()
        context['text'] = fb2.get_toc() + html
        return context


class UserCommentsView(generic.DetailView):
    model = User
    template_name = "webbooks/user_comments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        context['comments'] = Comment.objects.filter(userid=user.pk)
        return context


@require_POST
def post_comment(request, pk):
    book_id = pk
    book = get_object_or_404(Book, pk=book_id)
    text = request.POST["text"]
    userid = request.POST["userid"]
    user = User.objects.get(pk=userid)
    comment = Comment.objects.create(text=text, book=book,
        username=user.username, userid=userid)
    url = reverse("webbooks:book", args=[book_id])
    return HttpResponseRedirect(f"{url}#{comment.anchor()}")


def book_mimetype(path):
    suffix = Path(path).suffix
    if suffix == ".zip":
        return "application/x-zip-compressed-fb2"
    elif suffix == ".fb2":
        return "application/x-fictionbook+xml"
    raise TypeError("Unknown book extension.")


def download_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    handle = open(book.full_path(), 'rb')
    return FileResponse(handle, as_attachment=True,
        content_type=book_mimetype(book.full_path()))


def save_uploaded_book(uploaded_file):
    upload_dir = Path(conf.WEBBOOKS_UPLOAD)
    upload_dir.mkdir(parents=True, exist_ok=True)
    full_path = upload_dir / uploaded_file.name
    with open(full_path, "wb") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return full_path


def handle_uploaded_book(file):
    full_path = save_uploaded_book(file)
    book, _ = inspect_book(full_path)
    url = reverse("webbooks:book", args=[book.id])
    return HttpResponseRedirect(url)


def upload_book(request):
    context = {}
    if request.method == "POST":
        file = request.FILES.get("book_file", None)
        if file:
            return handle_uploaded_book(file)
        context["error_message"] = "No file uploaded"
    return render(request, "webbooks/upload_book.html", context)


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
