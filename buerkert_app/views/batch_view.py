from django.shortcuts import render
from django.views import View


class BatchView(View):

    def get(self, request, batch_id=None):
        context = {"batch_id": batch_id}
        return render(request, 'buerkert_app/batch_view.html', context)
