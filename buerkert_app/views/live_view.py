import asyncio

from asyncua import Client

from django.contrib import messages
from django.shortcuts import render
from django.views import View


class LiveView(View):
    url = "opc.tcp://localhost:4840/freeopcua/server/"
    namespace = "http://examples.freeopcua.github.io"

    async def get_data(self, request):
        exc = ""
        try:
            async with Client(url=self.url) as client:
                loop = asyncio.get_event_loop()
                # Find the namespace index
                nsidx = await client.get_namespace_index(self.namespace)

                # Get the variable node for read / write
                var = await client.nodes.root.get_child(["0:Objects", f"{nsidx}:MyObject", f"{nsidx}:MyVariable"])
                var1 = await client.nodes.root.get_child(["0:Objects", f"{nsidx}:MyObject", f"{nsidx}:MyVariable1"])
                var2 = await client.nodes.root.get_child(["0:Objects", f"{nsidx}:MyObject", f"{nsidx}:MyVariable2"])
                var3 = await client.nodes.root.get_child(["0:Objects", f"{nsidx}:MyObject", f"{nsidx}:MyVariable3"])
                value = await var.read_value()
                value1 = await var1.read_value()
                value2 = await var2.read_value()
                value3 = await var3.read_value()

                return [value, value1, value2, value3], []
        except TimeoutError:
            exc = f"TimeoutError: Can´t Connect to OPC-UA Server {self.url}"
            return [], [exc,]
        except Exception as e:
            exc = e
            return [], [exc,]


    def get(self, request):
        if request.htmx:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            values, opc_messages = loop.run_until_complete(self.get_data(request))
            loop.close()
            context = {"values": values, "opc_messages": opc_messages}
            return render(request, "snippets/data_values.html", context)
        return render(request, "buerkert_app/live_view.html")
