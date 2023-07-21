from django.http import FileResponse
from django.test import TestCase, Client
from django.urls import reverse


class TestDocumentView(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('documents')

    def test_DocumentView_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'buerkert_app/document_view.html')
        self.assertIsNotNone(response.context['documents'])

    def test_DocumentView_get_specific_document(self):
        filename = 'test_document.txt'  # replace with a valid document in your 'res/documents' directory
        response = self.client.get(self.url, {'document': filename})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response, FileResponse))
