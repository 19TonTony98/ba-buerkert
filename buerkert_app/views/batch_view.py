import datetime
import re

from django.contrib import messages
from django.shortcuts import render
from django.views import View

from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

from buerkert.settings import DATABASES
from buerkert_app.dashes.batch_dash import BatchDash
from buerkert_app.utils.utils import DATE_FORMAT

import warnings
from influxdb_client.client.warnings import MissingPivotFunction

warnings.simplefilter("ignore", MissingPivotFunction)


class BatchView(View):
    start = "00"+datetime.datetime(year=23, month=1, day=1).strftime(DATE_FORMAT)

    def get(self, request, batch_id=None):
        try:
            BatchDash('SimpleExample', request, batch_id)
        except Exception as e:
            messages.error(request, e)
            return render(request, 'base.html')

        context = {"batch_id": batch_id}
        return render(request, 'buerkert_app/batch_view.html', context)
