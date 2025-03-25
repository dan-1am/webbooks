from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views,apiviews


app_name = 'webbooks'

router = DefaultRouter()
router.register("authors", apiviews.AuthorViewSet, basename="api-author")
router.register("genres", apiviews.GenreViewSet, basename="api-genre")
router.register("sequences", apiviews.SequenceViewSet, basename="api-sequence")
router.register("books", apiviews.BookViewSet, basename="api-book")
#router.register("books", apiviews.BookViewSet, basename="book")

author_list = apiviews.AuthorViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

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
    path("upload_book", views.upload_book, name="upload_book"),
    path("book_exists<int:pk>", views.BookExistsView.as_view(), name="book_exists"),
    path("api/", include(router.urls)),
]

