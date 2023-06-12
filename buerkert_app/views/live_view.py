import asyncio

from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from buerkert_app.utils.collector_utils import is_container_running
from buerkert_app.utils.utils import get_opcua_data, ident_to_io, ios_to_displays, idents_to_ios


class LiveView(View):

    def get(self, request):
        if request.htmx:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            values, opc_messages = loop.run_until_complete(get_opcua_data())
            loop.close()
            io_list = idents_to_ios(values)
            display_list = ios_to_displays(io_list)
            display_list = sorted(display_list, key=lambda x: x['sps_port'])
            context = {"values": display_list, "opc_messages": opc_messages}
            return render(request, "snippets/data_values.html", context)

        context = {}
        batch = None
        running = None
        try:
            batch, running = is_container_running()
        except Exception as e:
            messages.error(request, e)
        form = UploadFileForm()
        context.update({"batch": batch, "running": running, "form": form})
        return render(request, "buerkert_app/live_view.html", context)

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES["file"])
            messages.success(request, "Datei erfolgreich hochgeladen")
        else:
            for error in form.errors['file']:
                messages.error(request, error)
        return self.get(request)


class UploadFileForm(forms.Form):
    file = forms.FileField(label="Neues Funktionsschema hochladen")

    def clean_file(self):
        data = self.cleaned_data['file']
        content_type = data.content_type
        if content_type == 'image/jpeg':
            return data
        else:
            raise ValidationError('Ungültiger Datentyp, Akzeptierte Datentypen: .jpg')


def handle_uploaded_file(f):
    with open("buerkert_app/static/buerkert_app/img/buerkert_funktionsschema.jpg", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
