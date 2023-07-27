from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory

from buerkert_app.views.live_view import LiveView


class TestLiveView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = LiveView()

    @patch("buerkert_app.views.live_view.get_opcua_data")
    def test_get_htmx(self, mock_get_data):
        mock_get_data.return_value = ([], [])
        request = self.factory.get('/')
        request.htmx = True
        response = self.view.get(request)
        self.assertEqual(response.status_code, 200)

    def test_get_not_htmx(self):
        request = self.factory.get('/')
        request.htmx = False
        response = self.view.get(request)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'buerkert_app/live_view.html')

    def test_post_valid_form(self):
        file_data = b'This is a test file.'
        test_file = SimpleUploadedFile('test_file.png', file_data)
        data = {"file": test_file}

        request = self.factory.post('/', data)
        request.FILES["file"] = test_file

        response = self.view.post(request)
        self.assertEqual(response.status_code, 200)

    def test_post_invalid_form(self):
        data = {"file": ""}

        request = self.factory.post('/', data)
        response = self.view.post(request)
        self.assertEqual(response.status_code, 200)
