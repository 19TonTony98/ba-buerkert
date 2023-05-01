from django.shortcuts import render
from django.views import View
from influxdb_client import InfluxDBClient

from buerkert_app.dashes.batch_dash import BatchDash


class BatchView(View):
    token = "LaQHo-7QN-pSfqHvgr7_4cDtnJHYl_zIXfAsO7j8RgjFLqw30jZnSMe_luq5yyCj4iWz8r3NQ6Ezs6ZxSv_bdg=="
    org = "41110e2dd2c8d5fe"
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
