import asyncio
import json
import os
import warnings

from asyncua import Client
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.warnings import MissingPivotFunction

from buerkert import settings
from buerkert.settings import DATABASES, IO_IDENT, SPS_CONF

warnings.simplefilter("ignore", MissingPivotFunction)

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


def io_to_ident(io, **kwargs):
    io_list = get_io_ident()
    for row in io_list:
        if io == row['sps_port']:
            return row['namespace_index'], row['identifier']


def ident_to_io(namespace_index, identifier, **kwargs):
    io_list = get_io_ident()
    for row in io_list:
        if namespace_index == row['namespace_index'] and identifier == row['identifier']:
            return row['sps_port']


def idents_to_ios(idents):
    io_list = get_io_ident()
    results = []
    for row in io_list:
        for ident in idents:
            if ident['namespace_index'] == row['namespace_index'] and ident['identifier'] == row['identifier']:
                results.append({"value": ident['value'], "sps_port": row['sps_port']})
    return results


def save_conf_list(conf_list):
    with open(SPS_CONF, "w") as fd:
        json.dump(conf_list, fd, indent=1)


def io_to_display(sps_port, **kwargs):
    conf_list = get_sps_conf_list()
    if disp_list := list(filter(lambda conf: conf.get('sps_port') == sps_port, conf_list)):
        return disp_list[0]
    else:
        return {}


def ios_to_displays(io_list, **kwargs):
    conf_list = get_sps_conf_list()
    results = []
    for ios in io_list:
        display = {}
        if disp_list := list(filter(lambda conf: conf.get('sps_port') == ios.get("sps_port"), conf_list)):
            display = {**disp_list[0], "value": ios['value']}
        results.append(display)
    return results


def get_sps_conf_list():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    values, _ = loop.run_until_complete(get_opcua_data())
    loop.close()

    if os.path.isfile(SPS_CONF):
        with open(SPS_CONF, "r") as fd:
            last_conf = json.load(fd)
    else:
        last_conf = []
    sps_conf = []

    for value in values:
        if not (ident := ident_to_io(value['namespace_index'], value['identifier'])):
            continue
        if last_confs := list(filter(lambda conf: conf.get('sps_port') == ident, last_conf)):
            sps_conf.extend(last_confs)
        else:
            sps_conf.append({"use": False, "sps_port": ident, "display": "", "unit": ""})
    save_conf_list(sps_conf)
    return sps_conf


def get_batch_ids(max_ids=1):
    with InfluxDBClient(**DATABASES["influx"]) as client:
        query_api = client.query_api()
        query = f'''
        from(bucket: "{DATABASES["influx"]["bucket"]}")
          |> range(start: -6mo)
          |> group(columns: ["_measurement"])
          |> min(column: "_time")
          |> sort(columns: ["_time"], desc: true)
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
