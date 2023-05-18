import json


def get_opcua_conf():
    with open("res/opcua_conf.json", "r") as fd:
        return json.load(fd)


def set_opcua_conf(conf):
    clean_conf = list(filter(lambda x: bool(x), conf))
    [row.pop('DELETE') for row in clean_conf]
    objects = []

    for row in clean_conf:
        obj, row['identifier'] = io_to_ident(row.pop('sps_port'))
        for obj_list in objects:
            if obj_list.get("object") != obj:
                continue
            variables = obj_list.get('variables', [])
            variables.append(row)
            obj_list['variables'] = variables
            break
        else:
            objects.append({"object": obj, "variables": [row]})

    with open("res/opcua_conf.json", "r") as fd:
        data = json.load(fd)
        if not data:
            raise FileNotFoundError("No Data in File")

    data['objects'] = objects

    with open("res/opcua_conf.json", "w") as fd:
        json.dump(data, fd, indent=1)


def get_io_ident():
    with open("res/io_ident.json", "r") as fd:
        return json.load(fd)


def io_to_ident(io):
    io_list = get_io_ident()
    for row in io_list:
        if io == row['sps_port']:
            return row['object'], row['identifier']


def ident_to_io(obj, ident):
    io_list = get_io_ident()
    for row in io_list:
        if obj == row['object'] and ident == row['identifier']:
            return row['sps_port']


def get_conf_list():
    opcua_conf = get_opcua_conf()
    sps_conf = []
    for obj in opcua_conf['objects']:
        for var in obj['variables']:
            sps_conf.append({"sps_port": ident_to_io(obj['object'], var['identifier']),
                             "display": var['display'],
                             "measurement": var['measurement']})
    return sps_conf


def create_telegraf_conf(batch_id):
    return


def start_telegraf(conf):
    return
