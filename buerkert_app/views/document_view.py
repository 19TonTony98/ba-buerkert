import os

from django.http import FileResponse
from django.shortcuts import render
from django.views import View


class DocumentView(View):

    def get(self, request):
        """
         Method to render the document view page.

        :param request: The HTTP request object.
        :return: The rendered HTML for the document view page.
        """
        document_root = os.path.join("res", "documents")
        # if a document is requested, is will be sent to download
        if document := request.GET.get("document"):
            filename = os.path.join(document_root, document)
            response = FileResponse(open(filename, 'rb'))
            return response
        # lists all document with name from the document folder
        documents = [document for document in os.listdir(document_root)]
        context = {"documents": documents}
        return render(request, 'buerkert_app/document_view.html', context)
