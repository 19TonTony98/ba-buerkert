import asyncio
import datetime
import json
import os
import warnings

import docker
from asyncua import Client
from background_task import background
from background_task.models import Task
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.warnings import MissingPivotFunction

from buerkert import settings
from buerkert.settings import DATABASES

warnings.simplefilter("ignore", MissingPivotFunction)

IO_IDENT = "res/io_ident.json"

SPS_CONF = "res/last_sps_conf.json"

TELEGRAF_IMAGE = "telegraf"

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


async def get_opcua_data():
    url = settings.OPCUA_URL
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


def get_io_ident():
    with open(IO_IDENT, "r") as fd:
        return json.load(fd)


def io_to_ident(io):
    io_list = get_io_ident()
    for row in io_list:
        if io == row['sps_port']:
            return row['namespace_index'], row['identifier']


def ident_to_io(obj, ident):
    io_list = get_io_ident()
    for row in io_list:
        if obj == row['namespace_index'] and ident == row['identifier']:
            return row['sps_port']


def get_conf_list():
    if not os.path.isfile(SPS_CONF):
        create_sps_conf()
    with open(SPS_CONF, "r") as fd:
        return json.load(fd)


def save_conf_list(conf_list):
    with open(SPS_CONF, "w") as fd:
        json.dump(conf_list, fd, indent=1)


def create_sps_conf():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    values, _ = loop.run_until_complete(get_opcua_data())
    loop.close()
    sps_conf = []
    for value in values:
        if not (ident := ident_to_io(value['namespace_index'], value['identifier'])):
            continue
        sps_conf.append({"use": False, "sps_port": ident, "display": "", "measurement": ""})
    save_conf_list(sps_conf)


def create_telegraf_conf(batch_dict, sps_list):
    batch_id = batch_dict['batch_id']
    sps_list = list(filter(lambda sps: sps.pop('use', False), sps_list))
    groups = {}
    for sps in sps_list:
        sps['DISPLAY_NAME'], sps['SENSOR_ID'] = sps.pop('display'), sps.pop('sps_port')
        sps['NSIDX'], sps['IDENTIFIER'] = io_to_ident(sps['SENSOR_ID'])
        namespace = groups.get(sps['NSIDX'], {})
        group = namespace.get(sps['measurement'], [])
        group.append(sps)
        namespace[sps.pop('measurement')] = group
        groups[sps.pop('NSIDX')] = namespace

    with open('res/templates/opcua/opcua_input_template', 'r') as file:
        input_tmpl = file.read()
    with open('res/templates/opcua/opcua_group_template', 'r') as file:
        group_tmpl = file.read()
    with open('res/templates/opcua/opcua_node_template', 'r') as file:
        node_tmpl = file.read()

    group_str = ""
    for nsidx, group in groups.items():
        node_str = ""
        for meas, values in group.items():
            for value in values:
                node_str += ("\n" + node_tmpl.format(MEASUREMENT=meas, **value))
        group_str += ("\n" + group_tmpl.format(BATCH_ID=batch_id, NSIDX=nsidx, NODES=node_str))
    input_str = ("\n" + input_tmpl.format(GROUPS=group_str, endpoint=settings.OPCUA_URL,
                                          **settings.DATABASES["influx"]))

    with open('res/telegraf.conf', 'w') as file:
        file.write(input_str)


def create_container(batch_id, start, end):
    # stop_telegraf()
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    if not client.images.list(name=TELEGRAF_IMAGE):
        print(f"pull {TELEGRAF_IMAGE}")
        client.images.pull(TELEGRAF_IMAGE)
    if containers := list(filter(lambda con: con.name.startswith(TELEGRAF_IMAGE), client.containers.list(all=True))):
        labels = containers[0].labels
        labels['start'] = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        labels['end'] = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else None
        return False, labels
    else:
        labels = {"batch_id": batch_id, "start": start.strftime(DATE_FORMAT),
                  "end": end.strftime(DATE_FORMAT) if end else None}
        client.containers.create(TELEGRAF_IMAGE, name=f"{TELEGRAF_IMAGE}_{batch_id}", detach=True, network_mode="host",
                                 labels=labels,
                                 volumes=[os.path.abspath('res/telegraf.conf') + ':/etc/telegraf/telegraf.conf',
                                          os.path.abspath('res/cert.pem') + ':/etc/telegraf/cert.pem',
                                          os.path.abspath('res/key.pem') + ':/etc/telegraf/key.pem', ])
        return True, labels


def stop_container():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    for container in list(filter(lambda con: con.name.startswith(TELEGRAF_IMAGE), client.containers.list(all=True))):
        if container.status == "running":
            container.kill()
        container.remove()
        print(f"stopped {container.name} {container.status}, normally stops at {container.labels['end']}")


@background(schedule=0)
def start_container():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    for container in list(filter(lambda con: con.name.startswith(TELEGRAF_IMAGE), client.containers.list(all=True))):
        name, labels = container.name, container.labels
        start = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        end = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else datetime.datetime.max
        if start <= datetime.datetime.now() < end:
            if container.status != "running":
                print(f"{container.name} {container.status}, starts at {container.labels['start']}")
                container.start()
            print(f"{container.name} {container.status}, stops at {container.labels['end']}")
        elif end and end < datetime.datetime.now():
            stop_container()
            print(f"{name} forced stops at {datetime.datetime.now()}")
            background_tasks = Task.objects.filter(task_name='buerkert_app.background_tasks.start_container')
            for background_task in background_tasks:
                background_task.delete()


def is_container_running():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    for con in list(filter(lambda con: con.name.startswith(TELEGRAF_IMAGE), client.containers.list(all=True))):
        labels = con.labels
        labels['start'] = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        labels['end'] = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else None
        print("status:" + con.status)
        return labels, con.status
    return None, None


def get_batch_ids(max_ids=1):
    with InfluxDBClient(**DATABASES["influx"]) as client:
        query_api = client.query_api()
        query = f'''
        from(bucket: "{DATABASES["influx"]["bucket"]}")
          |> range(start: 0)
          |> filter(fn: (r) => r._measurement =~ /[0-9]+/)
          |> group()
        '''
        if (df := query_api.query_data_frame(query)).empty:
            raise InfluxDBError(message="No Data found")
        df = df.rename(columns={"_time": "time", '_measurement': "batch_id"})
        df = df.sort_values(by=['time'], ascending=False).drop_duplicates(subset=['batch_id'])
        if len(batch_list := df.get(["batch_id", "time"]).to_dict('records')) > max_ids:
            batch_list = batch_list[:max_ids]
        return batch_list


def get_last_batch_id():
    return int(get_batch_ids()[0]["batch_id"])


# Zu test zwecken
if __name__ == "__main__":
    get_last_batch_id()
