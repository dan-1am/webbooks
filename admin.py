from django.contrib import admin

from .models import Book,Author,Sequence,Genre

class BookToAuthorInline(admin.TabularInline):
    model = Book.authors.through
    extra = 1

class BookAdmin(admin.ModelAdmin):
    inlines = [BookToAuthorInline]
    exclude = ["authors"]
    search_fields = ["title"]

class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "books"]
    inlines = [BookToAuthorInline]
    search_fields = ["name"]
    @admin.display(description="Books")
    def books(self, author):
        text = ",".join(b["title"] for b in author.book_set.values("title").all())
        return text

admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Sequence)
admin.site.register(Genre)
