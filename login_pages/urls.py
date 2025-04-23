from django.urls import path, include

from . import views


app_name = "login_pages"




urlpatterns = [
    path("", views.register_view, name="register"),
]
