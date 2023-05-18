from django import forms
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views import View

from buerkert_app.helpers import create_telegraf_conf, start_telegraf, get_conf_list, set_opcua_conf


class StartView(View):
    def get(self, request):
        context = {}
        form = BatchForm()
        formset = ConfFormSet(initial=get_conf_list())
        context.update({"form": form, "formset": formset})
        return render(request, "buerkert_app/start_view.html", context)

    def post(self, request):
        if request.GET.get("settings") == "save":
            formset = ConfFormSet(request.POST)
            if formset.is_valid():
                set_opcua_conf(formset.cleaned_data)
                messages.success(request, "Einstellungen gespeichert")
                return self.get(request)

        if request.htmx:
            formset = ConfFormSet(request.POST)
            if formset.is_valid():
                data = list(filter(lambda x: x.get('DELETE') == False, formset.cleaned_data))
                formset = ConfFormSet(initial=data)
            return render(request, "snippets/conf_setting_form.html", {"formset": formset})

        context = {}
        form = BatchForm(request.POST)
        formset = ConfFormSet(initial=get_conf_list())
        if form.is_valid():
            try:
                #ToDo telegraf conf
                create_telegraf_conf(form['batch_id'])
                start_telegraf("")
                messages.success(request, "Aufzeichnung gestartet")
                return redirect('live')
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, "Batch-ID ungültig")

        context.update({"form": form, "formset": formset})
        return render(request, "buerkert_app/start_view.html", context)


class BatchForm(forms.Form):
    batch_id = forms.CharField(label="Batch-ID")


class ConfForm(forms.Form):
    # ToDo ChoiceFiel for given sps port
    sps_port = forms.CharField(label="SPS I/O PORT")
    display = forms.CharField(label="Anzeige Name")
    measurement = forms.CharField(label="Einheit")


ConfFormSet = formset_factory(ConfForm, extra=1, can_delete=True)
