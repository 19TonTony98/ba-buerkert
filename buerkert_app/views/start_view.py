import datetime

from django import forms
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views import View
from bootstrap_datepicker_plus.widgets import DateTimePickerInput

from buerkert.settings import DATE_FORMAT
from buerkert_app.utils.collector_utils import stop_container, is_container_running, create_container, \
    create_config_file, start_container
from buerkert_app.utils.utils import get_sps_conf_list, save_conf_list, get_batch_ids
from res.units import Units


class StartView(View):
    def get(self, request):
        if request.GET.get("stop"):
            stop_container()
            return redirect('start')
        context = {}
        recent_batches = []
        batch = None
        new_id = ""
        running = None
        try:
            batch, running = is_container_running()
        except Exception as e:
            messages.error(request, e)
        try:
            recent_batches = get_batch_ids(10)
            last_id = int(max([batch['batch_id'] for batch in recent_batches]))
            new_id = last_id + 1
        except Exception as e:
            messages.error(request, e)
        form = BatchForm(initial={"batch_id": new_id, "start": datetime.datetime.now()})
        formset = ConfFormSet(initial=get_sps_conf_list())
        context.update({"form": form, "formset": formset, "batch": batch, "running": running,
                        "recent_batches": recent_batches})
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
            batch_id = form.cleaned_data['batch_id']
            batch_dict = form.cleaned_data.copy()
            batch_dict['start'] = batch_dict['start'].strftime(DATE_FORMAT)
            batch_dict['end'] = batch_dict['end'].strftime(DATE_FORMAT) if batch_dict['end'] else None
            save_conf_list(formset.cleaned_data)
            messages.success(request, "Einstellungen gespeichert")
            try:
                # ToDo telegraf conf
                create_config_file(form.cleaned_data, formset.cleaned_data)
                created, _ = create_container(**form.cleaned_data)
                if not created:
                    raise Exception("Ein Batch befindet sich in der Warteschlange")

                start_container(batch_dict=batch_dict)
                messages.success(request, f"Aufzeichnung für Batch-ID {batch_id} gestartet")
                return redirect('live')
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, "Ungültige Eingabe")

        context.update({"form": form, "formset": formset})
        return self.get(request)


class BatchForm(forms.Form):
    batch_id = forms.CharField(label="Batch-ID", required=False)
    start = forms.DateTimeField(label="Beginn", widget=DateTimePickerInput())
    end = forms.DateTimeField(label="Ende", widget=DateTimePickerInput(range_from='start'), required=False)


class ConfForm(forms.Form):
    # ToDo ChoiceFiel for given sps port
    use = forms.BooleanField(label="Aktiviert", widget=forms.CheckboxInput, required=False)
    sps_port = forms.CharField(label="SPS I/O PORT")
    display = forms.CharField(label="Anzeige Name")
    unit = forms.ChoiceField(label="Einheit", choices=[x.choice() for x in Units])


ConfFormSet = formset_factory(ConfForm, extra=0)
