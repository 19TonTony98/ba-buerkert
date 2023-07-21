import asyncio

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views import View

from buerkert_app.utils.collector_utils import is_container_running
from buerkert_app.utils.utils import get_opcua_data, ios_to_displays, idents_to_ios, handle_uploaded_file


class LiveView(View):

    def get(self, request):
        """
         Method to render the live view page or return live data as table for htmx request.

        :param request: The HTTP request object.
        :return: The rendered HTML for the live view page or datatable snippet.
        """
        if request.htmx:
            # establish Connection to opcua server, read data and return rendered table
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
            # check if container is running, for title
            batch, running = is_container_running()
        except Exception as e:
            messages.error(request, e)
        form = UploadFileForm()
        context.update({"batch": batch, "running": running, "form": form})
        return render(request, "buerkert_app/live_view.html", context)

    def post(self, request):
        """
         Method to save File and reloads page with new file.

        :param request: The HTTP request object.
        :return: The rendered HTML for the live view page.
        """
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # replace file if upload is valid
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
