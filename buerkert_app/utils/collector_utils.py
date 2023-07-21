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
    """
     Create a configuration file for the collector.

    :param batch_dict: A dictionary containing information about the batch.
    :param sps_list: A list of dictionaries containing information about the sps.
    :return: None
    """
    batch_id = batch_dict['batch_id']
    # filters only config that are used
    sps_list = list(filter(lambda sps: sps.pop('use', False), sps_list))
    data = {"batch_id": batch_id, "sps_list": sps_list, "io_ident": get_io_ident(), "url": settings.OPCUA_URL,
            "db": settings.DATABASES['influx']}
    with open(COLLECTOR_CONF, "w") as fd:
        json.dump(data, fd, indent=2)


def create_container(batch_id, start, end):
    """
     Create a Docker container with given batch ID, start and end date.

    :param batch_id: The ID of the batch.
    :param start: The start date of the batch.
    :param end: The end date of the batch (optional).
    :return: A tuple indicating whether the container was successfully created and the labels for the container.
    """
    # connect to docker host
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    # check if there is already an image
    if not client.images.list(name="influxdb_collector:dev"):
        print(f"build influxdb_collector")
        client.images.build(path="/home/app/influxdb_collector", tag="influxdb_collector:dev")

    labels = {"batch_id": batch_id, "start": start.strftime(DATE_FORMAT),
              "end": end.strftime(DATE_FORMAT) if end else None}
    return True, labels


def start_container(batch_dict):
    """
     Start a container with the given batch_dict.

    :param batch_dict: A dictionary containing information about the batch.
                       It should have the following keys:
                       - batch_id (str): The ID of the batch.
                       - start (str): The start time of the batch.
                       - end (str): The end time of the batch (optional).
    :return: None
    """
    print(f"start {batch_dict['batch_id']} at {batch_dict['start']}")
    # connect to docker host
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    # start container with parameters from batch_dict and bind volumes
    client.containers.run(image="influxdb_collector:dev", name=f"influxdb_collector_{batch_dict['batch_id']}",
                          network_mode='host', labels=batch_dict, auto_remove=True, detach=True,
                          volumes=['/var/run/:/var/run/',
                                   'shared_res:/home/app/influxdb_collector/res'])
    print(f"startet for {batch_dict['batch_id']}, stops at {batch_dict['end'] if batch_dict['end'] else 'never'}")


def stop_container():
    """
     Stops the running InfluxDB collector container(s).

    :return: None
    """
    # connect to docker host
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    # kill all collector containers
    for container in list(
            filter(lambda con: con.name.startswith("influxdb_collector"), client.containers.list(all=True))):
        if container.status == "running":
            container.kill()
        else:
            # remove if they didn´t remove themself
            container.remove()
        print(f"stopped {container.name} {container.status}, normally stops at {container.labels['end']}")


def is_container_running():
    """
     Check if a container named "influxdb_collector" is running.

    :return: A tuple containing the container labels and a boolean value indicating if the container is running.
    """
    # connect to docker host
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    # check all containers and return their labels if min one is running
    for con in list(filter(lambda con: con.name.startswith("influxdb_collector"), client.containers.list(all=True))):
        labels = con.labels
        labels['start'] = datetime.datetime.strptime(labels['start'], DATE_FORMAT)
        labels['end'] = datetime.datetime.strptime(labels['end'], DATE_FORMAT) if labels['end'] else None
        print("status:" + con.status)
        return labels, labels['start'] <= datetime.datetime.now() < \
                       (labels['end'] if labels['end'] else datetime.datetime.max)
    return None, None
