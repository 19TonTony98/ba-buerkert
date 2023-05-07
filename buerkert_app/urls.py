from django.urls import path, re_path

from buerkert_app.views.batch_view import BatchView
from buerkert_app.views.index import Index

urlpatterns = [
    path("", Index.as_view(), name="index"),
    re_path(r"batch/(?P<batch_id>\w+)", BatchView.as_view(), name='batch')
]