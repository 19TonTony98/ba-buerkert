import json


def get_opcua_conf():
    with open("res/opcua_conf.json", "r") as fd:
        return json.load(fd)

def set_opcua_conf(conf):
    with open("res/opcua_conf.json", "rw") as fd:
        old_data = json.load(fd)
        data = old_data
        json.dump(data, fd)


def get_io_ident():
    with open("res/io_ident.json", "r") as fd:
        return json.load(fd)


def io_to_ident(io):
    io_dict = get_io_ident()
    return io_dict.get(io)


def ident_to_io(ident):
    io_dict = get_io_ident()
    ident_dict = {value: key for key, value in io_dict.items()}
    return ident_dict.get(ident)


def get_conf_list():
    opcua_conf = get_opcua_conf()
    sps_conf = []
    for obj in opcua_conf['objects']:
        for var in obj['variables']:
            sps_conf.append({"sps_port": ident_to_io(var['identifier']),
                             "display_name": var['display'],
                             "measurement": var['measurement']})
    return sps_conf


def create_telegraf_conf(batch_id):
    return


def start_telegraf(conf):
    return
