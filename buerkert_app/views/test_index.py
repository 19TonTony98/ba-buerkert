from django.shortcuts import reverse
from django.test import TestCase, RequestFactory

from buerkert_app.views.index import Index


class TestIndexView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_no_batch_id_redirects_to_start(self):
        request = self.factory.get(reverse('index'))
        response = Index.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('start'))

    def test_with_batch_id_redirects_to_batch(self):
        request = self.factory.get(reverse('index'), data={'batch_id': 1})
        response = Index.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('batch', kwargs={'batch_id': 1}))
