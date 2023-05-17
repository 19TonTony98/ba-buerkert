import asyncio
import json

from asyncua import Client

from django.shortcuts import render
from django.views import View

from buerkert_app.helpers import get_opcua_conf


async def get_data():
    conf = get_opcua_conf()
    url = conf["url"]
    results = {}
    exc = []
    try:
        async with Client(url=url) as client:
            loop = asyncio.get_event_loop()
            # Find the namespace index
            nsidx = await client.get_namespace_index(conf["namespace"])

            # Get the variable node for read / write
            for obj in conf["objects"]:
                for variable in obj["variables"]:
                    var = await client.nodes.objects.get_child([f"{nsidx}:{obj['object']}",
                                                                f"{nsidx}:{variable['identifier']}"])
                    value = await var.read_value()
                    results.update({variable['display']: value})

    except TimeoutError:
        exc.append(f"TimeoutError: Can´t Connect to OPC-UA Server {url}")
    except Exception as e:
        exc.append(e)

    return results, exc


class LiveView(View):

    def get(self, request):
        if request.htmx:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            values, opc_messages = loop.run_until_complete(get_data())
            loop.close()
            context = {"values": values, "opc_messages": opc_messages}
            return render(request, "snippets/data_values.html", context)
        return render(request, "buerkert_app/live_view.html")
