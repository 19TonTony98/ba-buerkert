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
from buerkert_app.utils.utils import save_conf_list, get_batch_ids, get_possible_sps_conf_list
from res.units import Units


class StartView(View):
    def get(self, request):
        """
         Method to render the start view page, with option to stop container.

        :param request: The HTTP request object.
        :return: The rendered HTML for the start view page.
        """
        # if stop, stop container and reload
        if request.GET.get("stop"):
            stop_container()
            return redirect('start')
        context = {}
        recent_batches = []
        batch = None
        new_id = ""
        running = None
        # check if container is running, for title
        try:
            batch, running = is_container_running()
        except Exception as e:
            messages.error(request, e)
        try:
            # get last batches, for last batch list and next batch_id
            recent_batches = get_batch_ids(10)
            last_id = int(max([batch['batch_id'] for batch in recent_batches]))
            new_id = last_id + 1
        except Exception as e:
            messages.error(request, e)
        form = BatchForm(initial={"batch_id": new_id, "start": datetime.datetime.now()})
        # fill sps form with data from the last run
        formset = ConfFormSet(initial=get_possible_sps_conf_list())
        context.update({"form": form, "formset": formset, "batch": batch, "running": running,
                        "recent_batches": recent_batches})
        return render(request, "buerkert_app/start_view.html", context)

    def post(self, request):
        """
         Method to redirect the start view page, with option to save sps-settings and start container.

        :param request: The HTTP request object.
        :return: The rendered HTML for the start view page or live view page after success.
        """
        # if only settings are saved, validate and reload page
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
            # create new dict, to not change original dict
            batch_dict = form.cleaned_data.copy()
            # format time für collector usage
            batch_dict['start'] = batch_dict['start'].strftime(DATE_FORMAT)
            batch_dict['end'] = batch_dict['end'].strftime(DATE_FORMAT) if batch_dict['end'] else None
            # save sps settings
            save_conf_list(formset.cleaned_data)
            messages.success(request, "Einstellungen gespeichert")
            try:
                # create container config and create and start container, then show live page
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
    use = forms.BooleanField(label="Aktiviert", widget=forms.CheckboxInput, required=False)
    # sps should always be prefilled
    sps_port = forms.CharField(label="SPS I/O PORT")
    display = forms.CharField(label="Anzeige Name")
    unit = forms.ChoiceField(label="Einheit", choices=[x.choice() for x in Units])


# creates as many copy of ConfForm as namespace with sps-config are in io_ident.json defined
ConfFormSet = formset_factory(ConfForm, extra=0)
