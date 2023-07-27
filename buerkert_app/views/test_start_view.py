from django.test import RequestFactory, TestCase
from django.urls import reverse

from buerkert_app.views.start_view import StartView


class StartViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse('start')

    def test_start_view_get(self):
        request = self.factory.get(self.url)

        response = StartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'buerkert_app/start_view.html')

    def test_start_view_post(self):
        data = {}
        request = self.factory.post(self.url, data)

        response = StartView.as_view()(request)

        self.assertEqual(response.status_code, 302)
