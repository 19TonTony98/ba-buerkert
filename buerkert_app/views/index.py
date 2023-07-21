from django.shortcuts import redirect
from django.views import View


class Index(View):
    def get(self, request):
        """
         Method to redirect to the batch view page or start view page

        :param request: The HTTP request object.
        :return: The rendered HTML for the batch view page or start view page.
        """
        # if batch id from navbar search-field is given, it will be redirected
        if batch_id := request.GET.get("batch_id"):
            return redirect('batch', batch_id=batch_id)
        # else, redirect to start
        return redirect('start')
