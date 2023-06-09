import datetime
import os
import warnings

import docker
from background_task import background
from background_task.models import Task
from influxdb_client.client.warnings import MissingPivotFunction

from buerkert import settings
from buerkert.settings import DATE_FORMAT
from buerkert_app.utils.utils import io_to_ident

warnings.simplefilter("ignore", MissingPivotFunction)


TELEGRAF_IMAGE = "telegraf"


def create_config_file(batch_dict, sps_list):
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


@background(schedule=60)
def start_container(batch_dict=None):
    print("start")
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    print(list(filter(lambda con: con.name.startswith(TELEGRAF_IMAGE), client.containers.list(all=True))))
    for container in list(filter(lambda con: con.name.startswith(TELEGRAF_IMAGE), client.containers.list(all=True))):
        print("found")
        name, labels = container.name, container.labels
        start = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        end = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else datetime.datetime.max
        print(container.labels)
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
        return labels, con.status == "running"
    return None, None