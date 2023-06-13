import datetime

from django.contrib import messages
from django.shortcuts import render
from django.views import View

from buerkert_app.dashes.batch_dash import BatchDash
from buerkert_app.utils.utils import DATE_FORMAT

import warnings
from influxdb_client.client.warnings import MissingPivotFunction

warnings.simplefilter("ignore", MissingPivotFunction)


class BatchView(View):
    def get(self, request, batch_id=None):
        try:
            BatchDash('SimpleExample', request, batch_id)
        except Exception as e:
            messages.error(request, e)
            return render(request, 'base.html')

        context = {"batch_id": batch_id}
        return render(request, 'buerkert_app/batch_view.html', context)
