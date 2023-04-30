# Create your tests here.
from datetime import datetime

from influxdb_client import InfluxDBClient

if __name__ == "__main__":
    bucket = "sample-bucket"
    token = "LaQHo-7QN-pSfqHvgr7_4cDtnJHYl_zIXfAsO7j8RgjFLqw30jZnSMe_luq5yyCj4iWz8r3NQ6Ezs6ZxSv_bdg=="
    org = "41110e2dd2c8d5fe"
    start = datetime(year=2023, month=4, day=26)
    end = datetime(year=2023, month=4, day=27)

    query = f"""from(bucket: "sample-bucket")
                  |> range(start: -7d)
      """

    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)

    query_api = client.query_api()

    ## using Table structure
    tables = query_api.query(query)

    df = query_api.query_data_frame(query)

    for table in tables:
        print(table)
        for row in table.records:
            print(row.values)

    pass
