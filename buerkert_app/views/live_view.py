import asyncio

from django.shortcuts import render
from django.views import View

from buerkert_app.helpers import get_opcua_data, is_telegraf_running


class LiveView(View):

    def get(self, request):
        if request.htmx:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
            values, opc_messages = loop.run_until_complete(get_opcua_data())
            loop.close()
            context = {"values": values, "opc_messages": opc_messages}
            return render(request, "snippets/data_values.html", context)
        context = {}
        batch = is_telegraf_running()
        context.update({"batch": batch})
        return render(request, "buerkert_app/live_view.html", context)
