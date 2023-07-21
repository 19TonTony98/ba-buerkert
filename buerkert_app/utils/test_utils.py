from unittest.mock import patch, mock_open

from django.test import TestCase

from buerkert import settings
from buerkert_app.utils.utils import io_to_ident, get_io_ident, ident_to_io, idents_to_ios, \
    io_to_display, ios_to_displays


class TestGetIoIdent(TestCase):

    @patch('builtins.open', return_value=mock_open(read_data='{"key": "value"}').return_value)
    def test_get_io_ident(self, mock_open):
        self.assertEqual(get_io_ident(), {'key': 'value'})
        mock_open.assert_called_once_with(settings.IO_IDENT, 'r')


class TestIOToIdent(TestCase):

    @patch('buerkert_app.utils.utils.get_io_ident', autospec=True)
    def test_io_to_ident(self, mock_get_io_ident):
        mock_get_io_ident.return_value = [
            {'sps_port': 'port1', 'namespace_index': 'index1', 'identifier': 'identifier1'},
            {'sps_port': 'port2', 'namespace_index': 'index2', 'identifier': 'identifier2'},
        ]

        result = io_to_ident('port1')
        self.assertEqual(result, ('index1', 'identifier1'))

        result = io_to_ident('port2')
        self.assertEqual(result, ('index2', 'identifier2'))

        result = io_to_ident('port_that_does_not_exist')
        self.assertIsNone(result)


class TestIdentToIO(TestCase):

    @patch('buerkert_app.utils.utils.get_io_ident')
    def test_ident_to_io(self, mock_get_io_ident):
        mock_get_io_ident.return_value = [
            {'namespace_index': 1, 'identifier': 'A', 'sps_port': 'P1'},
            {'namespace_index': 2, 'identifier': 'B', 'sps_port': 'P2'},
        ]

        sps_port = ident_to_io(1, 'A')
        self.assertEqual(sps_port, 'P1')

        sps_port = ident_to_io(3, 'C')
        self.assertIsNone(sps_port)


class TestIdentsToIos(TestCase):

    @patch('buerkert_app.utils.utils.get_io_ident')
    def test_idents_to_ios(self, mock_get_io_ident):
        idents = [
            {"namespace_index": 1, "identifier": "a", "value": 123},
            {"namespace_index": 2, "identifier": "b", "value": 456},
        ]

        mock_get_io_ident.return_value = [
            {"namespace_index": 1, "identifier": "a", "sps_port": "port1"},
            {"namespace_index": 2, "identifier": "b", "sps_port": "port2"},
        ]

        expected_output = [
            {"value": 123, "sps_port": "port1"},
            {"value": 456, "sps_port": "port2"},
        ]

        result = idents_to_ios(idents)
        self.assertEqual(result, expected_output)


class TestIOTODISPLAY(TestCase):
    @patch('buerkert_app.utils.utils.get_sps_conf_list')
    def test_io_to_display(self, get_sps_conf_list):
        get_sps_conf_list.return_value = [
            {'sps_port': 1, 'display': 'display1'},
            {'sps_port': 2, 'display': 'display2'},
            {'sps_port': 3, 'display': 'display3'},
        ]

        self.assertDictEqual(io_to_display(1), {'sps_port': 1, 'display': 'display1'})
        self.assertDictEqual(io_to_display(2), {'sps_port': 2, 'display': 'display2'})
        self.assertDictEqual(io_to_display(3), {'sps_port': 3, 'display': 'display3'})
        self.assertDictEqual(io_to_display(4), {})


class TestIosToDisplays(TestCase):
    @patch('buerkert_app.utils.utils.get_sps_conf_list')
    def test_ios_to_displays(self, mock_get_sps_conf_list):
        # Set the return value of the function mock
        mock_get_sps_conf_list.return_value = [{'sps_port': 1, 'display': 'display1'},
                                               {'sps_port': 2, 'display': 'display2'}]

        test_data = [{'sps_port': 1, 'value': 'value1'},
                     {'sps_port': 2, 'value': 'value2'}]

        expected_data = [{'sps_port': 1, 'display': 'display1', 'value': 'value1'},
                         {'sps_port': 2, 'display': 'display2', 'value': 'value2'}]

        result = ios_to_displays(test_data)

        # Mock function is called once
        mock_get_sps_conf_list.assert_called_once()

        self.assertEqual(result, expected_data)
