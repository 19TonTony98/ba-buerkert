import asyncio
import json
import os

from asyncua import Client
import docker

from buerkert import settings

IO_IDENT = "res/io_ident.json"

SPS_CONF = "res/last_sps_conf.json"

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
                node_str += ("\n" + node_tmpl.format(MEASURMENT=meas, **value))
        group_str += ("\n" + group_tmpl.format(BATCH_ID=batch_id, NSIDX=nsidx, NODES=node_str))
    input_str = ("\n" + input_tmpl.format(GROUPS=group_str))
    input_str = input_str.format(**settings.DATABASES["influx"])

    with open('res/telegraf.conf', 'w') as file:
        file.write(input_str)


def start_telegraf(conf):
    img = "hello_world"
    client = docker.from_env()
    if not client.images.list(filters=img):
        print(f"pull {img}")
        client.pull(img)
    print(f"run {img}")
    client.containers.run(img)



# Zu test zwecken
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    values, opc_messages = loop.run_until_complete(get_opcua_data())
    loop.close()
