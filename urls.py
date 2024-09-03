from django.urls import path

from . import views

app_name = 'webbooks'

urlpatterns = [
    path("", views.index, name="index"),
    path("authors/", views.IndexView.as_view(), name="authors"),
    path("duplicates/", views.DuplicatesView.as_view(), name="duplicates"),
    path("author<int:pk>/", views.AuthorView.as_view(), name="author"),
    path("book<int:pk>/", views.BookView.as_view(), name="book"),
    path("read<int:pk>/", views.ReadView.as_view(), name="read"),
    path("user<int:pk>/", views.UserCommentsView.as_view(), name="user_comments"),
    path("book<int:pk>/comment", views.post_comment, name="comment"),
    path("book<int:pk>/download", views.download_book, name="download_book"),
]
