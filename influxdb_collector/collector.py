import asyncio
import datetime
import json
import time

import pytz

import docker
from asyncua import Client
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

berlin_timezone = pytz.timezone('Europe/Berlin')
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def ident_to_io(io_list, obj, ident):
    for row in io_list:
        if obj == row['namespace_index'] and ident == row['identifier']:
            return row['sps_port']


async def get_opcua_data(url):
    results = []
    excs = []
    try:
        async with Client(url=url) as client:
            loop = asyncio.get_event_loop()
            nodes = await client.get_objects_node().get_children()
            for node in nodes[2:]:
                br_name = await node.read_browse_name()
                node_name = br_name.Name
                nsidx = br_name.NamespaceIndex
                for var in await node.get_variables():
                    identifier = var.nodeid.Identifier
                    name = await var.read_browse_name()
                    value = await var.read_value()
                    results.append({"node_name": node_name, "namespace_index": nsidx, "identifier": identifier,
                                    "variable_name": name.Name, "value": value})
    except TimeoutError:
        excs.append(f"TimeoutError: Can´t Connect to OPC-UA Server {url}")
    except Exception as e:
        excs.append(e)

    return results, excs


def collector(batch_id, sps_list, io_ident, url, db):
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    while True:
        container = list(filter(lambda con: con.name.startswith("influxdb_collector"),
                                client.containers.list(all=True)))[0]
        name, labels = container.name, container.labels
        start = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        end = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else \
            datetime.datetime.max - datetime.timedelta(days=1)
        start = berlin_timezone.localize(start)
        end = berlin_timezone.localize(end)
        now = datetime.datetime.now(berlin_timezone)

        if start <= now < end:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop = asyncio.get_event_loop()
                values, opc_messages = loop.run_until_complete(get_opcua_data(url))
                if opc_messages:
                    raise Exception(opc_messages)
                loop.close()

                points = []
                for value in values:
                    sps_port = ident_to_io(io_ident, value['namespace_index'], value['identifier'])
                    display_name = list(filter(lambda row: row['sps_port'] == sps_port, sps_list))
                    if not sps_port or not display_name:
                        continue
                    else:
                        display_name = display_name[0]
                    tags = {"display": display_name['display'], "sensor_id": sps_port}
                    fields = {display_name['measurement']: value['value']}
                    points.append({"measurement": int(batch_id), "tags": tags, "fields": fields})

                with InfluxDBClient(**db) as influxdb_client:
                    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
                    write_api.write(bucket=db['bucket'], org=db['org'], record=points)
                    print("Added:")
                    print(points)

            except Exception as e:
                print(e)
        elif end < now:
            print(f"ending {batch_id}")
            if container.status == "running":
                container.kill()
            else:
                container.remove()
        time.sleep(1)


if __name__ == "__main__":
    with open("/home/app/conf/conf.json", "r") as fd:
        data = json.load(fd)
    print(f"container {data['batch_id']} startet and idle")
    collector(**data)
