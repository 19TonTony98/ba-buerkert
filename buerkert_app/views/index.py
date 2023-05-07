from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View


class Index(View):
    def get(self, request):
        if batch_id := request.GET.get("batch_id"):
            return redirect('batch', batch_id=batch_id)
        context = {}
        return render(request, "base.html", context)
