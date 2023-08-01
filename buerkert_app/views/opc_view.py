import asyncio

from django.shortcuts import render
from django.views import View

from buerkert_app.utils.utils import get_opcua_data


class OPCView(View):

    def get(self, request):
        if request.htmx:
            # establish Connection to opcua server, read data and return rendered table
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            values, opc_messages = loop.run_until_complete(get_opcua_data())
            loop.close()
            context = {"values": values, "opc_messages": opc_messages}
            return render(request, "snippets/opcua_data_values.html", context)

        return render(request, "buerkert_app/opc_view.html")
