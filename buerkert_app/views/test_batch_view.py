from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase, RequestFactory

from buerkert_app.views.batch_view import BatchView


class TestBatchView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = BatchView.as_view()

    @patch('buerkert_app.views.batch_view.BatchDash')
    def test_get_with_batch_id(self, mock_batch_dash):
        # Setup
        batch_id = '1'
        request = self.factory.get(f'/batch/{batch_id}')

        response = self.view(request, batch_id=batch_id)

        # Validate
        mock_batch_dash.assert_called_once_with('SimpleExample', request, batch_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name[0], 'buerkert_app/batch_view.html')

    @patch('buerkert_app.views.batch_view.BatchDash')
    def test_get_raises_exception(self, mock_batch_dash):
        # Setup
        mock_batch_dash.side_effect = Exception('Test Exception')
        batch_id = '1'
        request = self.factory.get(f'/batch/{batch_id}')

        response = self.view(request, batch_id=batch_id)

        # Validate
        mock_batch_dash.assert_called_once_with('SimpleExample', request, batch_id)
        messages = list(get_messages(request))
        self.assertEqual(str(messages[0]), 'Test Exception')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name[0], 'base.html')
