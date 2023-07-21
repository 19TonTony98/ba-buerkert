import os

from django.http import FileResponse
from django.shortcuts import render
from django.views import View


class DocumentView(View):
    #config in yaml and cleanup
    def get(self, request):
        document_root = os.path.join("res", "documents")
        if document := request.GET.get("document"):
            filename = os.path.join(document_root, document)
            response = FileResponse(open(filename, 'rb'))
            return response
        documents = [document for document in os.listdir(document_root)]
        context = {"documents": documents}
        return render(request, 'buerkert_app/document_view.html', context)
