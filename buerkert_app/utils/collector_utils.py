import datetime
import json
import warnings

import docker
from influxdb_client.client.warnings import MissingPivotFunction

from buerkert import settings
from buerkert.settings import DATE_FORMAT, COLLECTOR_CONF
from buerkert_app.utils.utils import get_io_ident

warnings.simplefilter("ignore", MissingPivotFunction)


def create_config_file(batch_dict, sps_list):
    batch_id = batch_dict['batch_id']
    sps_list = list(filter(lambda sps: sps.pop('use', False), sps_list))
    data = {"batch_id": batch_id, "sps_list": sps_list, "io_ident": get_io_ident(), "url": settings.OPCUA_URL,
            "db": settings.DATABASES['influx']}
    with open(COLLECTOR_CONF, "w") as fd:
        json.dump(data, fd, indent=2)


def create_container(batch_id, start, end):
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    if not client.images.list(name="influxdb_collector:dev"):
        print(f"build influxdb_collector")
        client.images.build(path="/home/app/influxdb_collector", tag="influxdb_collector:dev")

    labels = {"batch_id": batch_id, "start": start.strftime(DATE_FORMAT),
              "end": end.strftime(DATE_FORMAT) if end else None}
    return True, labels


def start_container(batch_dict):
    print(f"start {batch_dict['batch_id']} at {batch_dict['start']}")
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.containers.run(image="influxdb_collector:dev", name=f"influxdb_collector_{batch_dict['batch_id']}",
                          network_mode='host', labels=batch_dict, auto_remove=True, detach=True,
                          volumes=['/var/run/:/var/run/',
                                   'shared_res:/home/app/influxdb_collector/res'])
    print(f"startet for {batch_dict['batch_id']}, stops at {batch_dict['end'] if batch_dict['end'] else 'never'}")


def stop_container():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    for container in list(
            filter(lambda con: con.name.startswith("influxdb_collector"), client.containers.list(all=True))):
        if container.status == "running":
            container.kill()
        else:
            container.remove()
        print(f"stopped {container.name} {container.status}, normally stops at {container.labels['end']}")


def is_container_running():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    for con in list(filter(lambda con: con.name.startswith("influxdb_collector"), client.containers.list(all=True))):
        labels = con.labels
        labels['start'] = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        labels['end'] = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else None
        print("status:" + con.status)
        return labels, labels['start'] <= datetime.datetime.now() < \
                       (labels['end'] if labels['end'] else datetime.datetime.max)
    return None, None
