import datetime

from django.contrib import messages
from django.shortcuts import render
from django.views import View

from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

from buerkert.settings import DATABASES
from buerkert_app.dashes.batch_dash import BatchDash


class BatchView(View):
    start = datetime.datetime(year=23, month=1, day=1).strftime("%Y-%m-%dT%H:%M:%SZ")

    def get(self, request, batch_id=None):
        try:
            with InfluxDBClient(**DATABASES["influx"]) as client:
                query_api = client.query_api()
                query = f"""from(bucket: "{DATABASES["influx"]["bucket"]}")
                              |> range(start: 00{self.start})
                              |> filter(fn: (r) => r._measurement == "{batch_id}")
                         """

                if (df := query_api.query_data_frame(query)).empty:
                    raise InfluxDBError(message="No Data found")
        except Exception as e:
            messages.error(request, e)
            return render(request, 'base.html')

        BatchDash('SimpleExample', df, "_field", x="_time", y="_value", color='sensor_id')

        context = {"batch_id": batch_id}
        return render(request, 'buerkert_app/batch_view.html', context)
