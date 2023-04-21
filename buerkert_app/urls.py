from django.urls import path

from buerkert_app.views.index import Index

urlpatterns = [
    path("", Index.as_view(), name="index"),
]