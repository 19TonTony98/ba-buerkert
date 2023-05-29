from django import forms
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views import View

from buerkert_app.helpers import create_telegraf_conf, start_telegraf, get_conf_list, save_conf_list


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
                save_conf_list(formset.cleaned_data)
                messages.success(request, "Einstellungen gespeichert")
            else:
                messages.error(request, "Einstellungen konnten nicht gespeichert werden")
            return redirect('start')

        context = {}
        form = BatchForm(request.POST)
        formset = ConfFormSet(request.POST)
        if not request.POST.get("batch_id"):
            messages.error(request, "Batch-ID ungültig")
        elif form.is_valid() and formset.is_valid():
            save_conf_list(formset.cleaned_data)
            messages.success(request, "Einstellungen gespeichert")
            try:
                #ToDo telegraf conf
                create_telegraf_conf(form.cleaned_data, formset.cleaned_data)
                start_telegraf("")
                messages.success(request, "Aufzeichnung gestartet")
                return redirect('live')
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, "Ungültige Eingabe")

        context.update({"form": form, "formset": formset})
        return render(request, "buerkert_app/start_view.html", context)


class BatchForm(forms.Form):
    batch_id = forms.CharField(label="Batch-ID", required=False)


class ConfForm(forms.Form):
    # ToDo ChoiceFiel for given sps port
    use = forms.BooleanField(label=" ", widget=forms.CheckboxInput, required=False)
    sps_port = forms.CharField(label="SPS I/O PORT")
    display = forms.CharField(label="Anzeige Name")
    measurement = forms.CharField(label="Einheit")


ConfFormSet = formset_factory(ConfForm, extra=0)
