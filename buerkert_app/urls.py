from django.urls import path, re_path

from buerkert_app.views.batch_view import BatchView
from buerkert_app.views.document_view import DocumentView
from buerkert_app.views.index import Index
from buerkert_app.views.live_view import LiveView
from buerkert_app.views.start_view import StartView
from buerkert_app.views.opc_view import OPCView

urlpatterns = [
    path("", Index.as_view(), name="index"),
    re_path(r"batch/(?P<batch_id>\w+)", BatchView.as_view(), name='batch'),
    path(r"live/", LiveView.as_view(), name='live'),
    path(r"start/", StartView.as_view(), name='start'),
    path(r"documents/", DocumentView.as_view(), name='documents'),
    # only for admin, all nodes send from opcua, which can be added to io_ident.json
    path(r"opcua/", OPCView.as_view(), name='opcua')
]
