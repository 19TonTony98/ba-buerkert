import asyncio
import json
import os
import warnings

from asyncua import Client
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.warnings import MissingPivotFunction

from buerkert import settings
from buerkert.settings import DATABASES, IO_IDENT, SPS_CONF, F_SCHEMA_PATH

warnings.simplefilter("ignore", MissingPivotFunction)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


async def get_opcua_data():
    """
    This method asynchronously retrieves data from an OPC-UA server using the provided URL. It returns a tuple
    containing the results and any exceptions encountered during the process.

    :return: A tuple containing the results and exceptions
    """
    url = settings.OPCUA_URL
    results = []
    excs = []
    try:
        async with Client(url=url) as client:
            loop = asyncio.get_event_loop()
            nodes = await client.get_objects_node().get_children()
            # first two irrelevant, just generic data
            for node in nodes[2:]:
                # read node_name and namespace from node
                br_name = await node.read_browse_name()
                node_name = br_name.Name
                nsidx = br_name.NamespaceIndex
                # get var name and value from every var in node and append them
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
    """
    Reads the IO_IDENT file and returns its contents as a JSON object.

    :return: The contents of the IO_IDENT file as a JSON object.t
    """
    with open(IO_IDENT, "r") as fd:
        return json.load(fd)


def io_to_ident(io, **kwargs):
    """
    :param io: Input/output value to match against the 'sps_port' field in the io_list
    :param kwargs: Additional keyword arguments if needed (not used in this method)
    :return: A tuple containing the 'namespace_index' and 'identifier' values for the matched 'sps_port' in the io_list
    """
    io_list = get_io_ident()
    for row in io_list:
        if io == row['sps_port']:
            return row['namespace_index'], row['identifier']


def ident_to_io(namespace_index, identifier, **kwargs):
    """
     Maps an identifier to an IO port based on the given namespace index and identifier.

    :param namespace_index: The namespace index for the IO port.
    :param identifier: The identifier for the IO port.
    :param kwargs: Additional keyword arguments.
    :return: The SPS port associated with the identifier and namespace index.
    """
    io_list = get_io_ident()
    for row in io_list:
        if namespace_index == row['namespace_index'] and identifier == row['identifier']:
            return row['sps_port']


def idents_to_ios(idents):
    """
    Converts a list of identifiers to the corresponding I/O values.

    :param idents: A list of dictionaries representing the identifiers to convert.
        Each dictionary must have the following keys:
        - 'namespace_index': The namespace index of the identifier.
        - 'identifier': The identifier value.
    :return: A list of dictionaries representing the converted I/O values. Each dictionary will have the following keys:
        - 'value': The value of the identifier.
        - 'sps_port': The corresponding SPS port for the identifier.
    """
    io_list = get_io_ident()
    results = []
    for row in io_list:
        for ident in idents:
            if ident['namespace_index'] == row['namespace_index'] and ident['identifier'] == row['identifier']:
                results.append({"value": ident['value'], "sps_port": row['sps_port']})
    return results


def save_conf_list(conf_list):
    """
    Save the configuration list to a file.

    :param conf_list: The configuration list to be saved.
    :return: None
    """
    with open(SPS_CONF, "w") as fd:
        json.dump(conf_list, fd, indent=1)


def io_to_display(sps_port, **kwargs):
    """
    Get Displayname to io

    :param sps_port: The SPS port number to search for in the configuration list.
    :return: The first matching display configuration dictionary
    corresponding to the given SPS port number in the configuration list. Returns an empty dictionary if no match is
    found.
    """
    conf_list = get_sps_conf_list()
    if disp_list := list(filter(lambda conf: conf.get('sps_port') == sps_port, conf_list)):
        return disp_list[0]
    else:
        return {}


def ios_to_displays(io_list, **kwargs):
    """
    :param io_list: List of dictionaries containing IO information.
    :param kwargs: Optional keyword arguments.
    :return: List of dictionaries representing displays.
    """
    conf_list = get_sps_conf_list()
    results = []
    for ios in io_list:
        if disp_list := list(filter(lambda conf: conf.get('sps_port') == ios.get("sps_port"), conf_list)):
            display = {**disp_list[0], "value": ios['value']}
            results.append(display)
    return results


def get_sps_conf_list():
    """
     Returns a dictionary containing the contents of the SPS_CONF file.

    :return: A dictionary with the contents of the SPS_CONF file.
    """
    if os.path.isfile(SPS_CONF):
        with open(SPS_CONF, "r") as fd:
            return json.load(fd)
    return {}


def get_possible_sps_conf_list():
    """
    Get every possible sps, possible sps are which are in namespace from opcua server and
     connection from namespace to sps in io_ident.json. saves the last config in last_config.json, and updates
     these if necessary

    :return: A list of possible SPS configurations.
    """
    # connect to opcua and get data
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    values, _ = loop.run_until_complete(get_opcua_data())
    loop.close()

    # open last config or create
    if os.path.isfile(SPS_CONF):
        with open(SPS_CONF, "r") as fd:
            last_conf = json.load(fd)
    else:
        last_conf = []
    sps_conf = []

    for value in values:
        # get sps port from namespace if given
        if not (ident := ident_to_io(value['namespace_index'], value['identifier'])):
            continue
        # check if the sps port has a display name from last time
        if last_confs := list(filter(lambda conf: conf.get('sps_port') == ident, last_conf)):
            sps_conf.extend(last_confs)
        else:
            # else, append as new sps port
            sps_conf.append({"use": False, "sps_port": ident, "display": "", "unit": ""})

    # if connection to opcua server, return new conf, else last config
    if values:
        return sps_conf
    else:
        return last_conf


def get_batch_ids(max_ids=1):
    """
     Retrieve a list of batch IDs from InfluxDB.

    :param max_ids: Maximum number of batch IDs to retrieve. Default is 1.
    :type max_ids: int
    :return: List of dictionaries containing batch IDs and times.
    :rtype: list[dict]
    :raises InfluxDBError: If no data is found in InfluxDB.
    """
    with InfluxDBClient(**DATABASES["influx"]) as client:
        query_api = client.query_api()
        query = f'''
        from(bucket: "{DATABASES["influx"]["bucket"]}")
          |> range(start: -6mo)
          |> group(columns: ["_measurement"])
          |> min(column: "_time")
          |> sort(columns: ["_time"], desc: true)
        '''
        # if the is no data, raise error to display in message
        if (df := query_api.query_data_frame(query)).empty:
            raise InfluxDBError(message="No Data found")
        # rename columns for better usage and sort after the newest
        df = df.rename(columns={"_time": "time", '_measurement': "batch_id"})
        df = df.sort_values(by=['time'], ascending=False).drop_duplicates(subset=['batch_id'])
        # return as many id as needed or all
        if len(batch_list := df.get(["batch_id", "time"]).to_dict('records')) > max_ids:
            batch_list = batch_list[:max_ids]
        return batch_list


def get_last_batch_id():
    """
    Retrieve the last batch ID from the list of batch IDs.

    :return: The last batch ID as an integer.
    """
    return int(get_batch_ids()[0]["batch_id"])


def handle_uploaded_file(file):
    """
    :param file: The uploaded file object to be handled.
    :return: None
    """
    with open(F_SCHEMA_PATH, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)


# for test usage
if __name__ == "__main__":
    get_last_batch_id()
