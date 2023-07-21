from django.contrib import messages
from django.shortcuts import render
from django.views import View

from buerkert_app.dashes.batch_dash import BatchDash

import warnings
from influxdb_client.client.warnings import MissingPivotFunction

warnings.simplefilter("ignore", MissingPivotFunction)


class BatchView(View):
    def get(self, request, batch_id=None):
        """
         Method to render the batch view page.

        :param request: The HTTP request object.
        :param batch_id: The ID of the batch (default: None).
        :return: The rendered HTML for the batch view page.
        """
        try:
            # start dash with a name
            BatchDash('SimpleExample', request, batch_id)
        except Exception as e:
            # shows message if error occurs
            messages.error(request, e)
            return render(request, 'base.html')

        # add batch_id for title name
        context = {"batch_id": batch_id}
        return render(request, 'buerkert_app/batch_view.html', context)
