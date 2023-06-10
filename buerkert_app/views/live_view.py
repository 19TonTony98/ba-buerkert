import asyncio

from django.contrib import messages
from django.shortcuts import render
from django.views import View

from buerkert_app.utils.collector_utils import is_container_running
from buerkert_app.utils.utils import get_opcua_data, ident_to_io, io_to_displayname


class LiveView(View):

    def get(self, request):
        if request.htmx:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            values, opc_messages = loop.run_until_complete(get_opcua_data())
            loop.close()
            io_list = [{'sps_port': ident_to_io(**value), 'value': value['value']} for value in values]
            io_list = list(filter(lambda x: x.get('sps_port'), io_list))
            display_list = [{**io_to_displayname(**value), 'value': value['value']} for value in io_list]
            display_list = sorted(display_list, key=lambda x: x['sps_port'])
            context = {"values": display_list, "opc_messages": opc_messages}
            return render(request, "snippets/data_values.html", context)

        context = {}
        batch = None
        running = None
        try:
            batch, running = is_container_running()
        except Exception as e:
            messages.error(request, e)
        context.update({"batch": batch, "running": running})
        return render(request, "buerkert_app/live_view.html", context)
