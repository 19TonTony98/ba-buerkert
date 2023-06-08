from django.shortcuts import redirect
from django.views import View


class Index(View):
    def get(self, request):
        if batch_id := request.GET.get("batch_id"):
            return redirect('batch', batch_id=batch_id)
        return redirect('start')
