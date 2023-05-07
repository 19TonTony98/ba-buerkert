from django.shortcuts import render
from django.views import View
from influxdb_client import InfluxDBClient

from buerkert_app.dashes.batch_dash import BatchDash


class BatchView(View):
    token = "hDobQ3-fzXSY2FxGqz2iZBsFjKcZE6q9NN1Z6m2eszwZj77LFkpYb4EPDDUG6GbBgGS9TkbuH_vhmmEFXG9LbQ=="
    org = "HSWT"
    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    query_api = client.query_api()

    def get(self, request, batch_id=None):
        query = f"""from(bucket: "sample-bucket")
                      |> range(start: -30d)
                 """
        df = self.query_api.query_data_frame(query)
        BatchDash('SimpleExample', df, "_field", x="_time", y="_value", color='sensor_id')

        context = {"batch_id": batch_id}
        return render(request, 'buerkert_app/batch_view.html', context)
