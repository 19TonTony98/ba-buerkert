import asyncio
from unittest.mock import patch, mock_open, MagicMock

from django.test import TestCase

from buerkert import settings
from buerkert_app.utils.utils import io_to_ident, get_io_ident, ident_to_io, idents_to_ios, \
    io_to_display, ios_to_displays, get_opcua_data, get_possible_sps_conf_list, get_batch_ids, get_last_batch_id


class TestGetOpcUaData(TestCase):
    class TestNode:
        async def read_browse_name(self):
            return MagicMock(Name='Test', NamespaceIndex=1)

        async def get_variables(self):
            return [MagicMock(read_browse_name=self.read_browse_name, read_value=self.read_value)]

        async def read_value(self):
            return 'TestValue'

    @patch('buerkert_app.utils.utils.Client', autospec=True)
    def test_get_opcua_data_exception(self, mock_client):
        mock_client.side_effect = TimeoutError()
        expected_exception_message = f"TimeoutError: Can´t Connect to OPC-UA Server {settings.OPCUA_URL}"

        loop = asyncio.get_event_loop()
        results, exceptions = loop.run_until_complete(get_opcua_data())

        self.assertListEqual(results, [])
        self.assertListEqual(exceptions, [expected_exception_message])


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


class TestGetPossibleSPSConfList(TestCase):

    @patch('buerkert_app.utils.utils.get_opcua_data',
           return_value=([{'namespace_index': 1, 'identifier': '123'}], None))
    @patch('buerkert_app.utils.utils.ident_to_io', return_value='123')
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open, read_data='[]')
    @patch('os.path.isfile', return_value=True)
    def test_get_possible_sps_conf_list_with_file(self, *_):
        result = get_possible_sps_conf_list()
        self.assertEqual(result, [{'use': False, 'sps_port': '123', 'display': '', 'unit': ''}])

    @patch('buerkert_app.utils.utils.get_opcua_data',
           return_value=([{'namespace_index': 1, 'identifier': '123'}], None))
    @patch('buerkert_app.utils.utils.ident_to_io', return_value=None)
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open, read_data='[]')
    @patch('os.path.isfile', return_value=False)
    def test_get_possible_sps_conf_list_without_file(self, *_):
        result = get_possible_sps_conf_list()
        self.assertEqual(result, [])


class TestGetBatchIds(TestCase):

    @patch('buerkert_app.utils.utils.InfluxDBClient')
    def test_get_batch_ids(self, MockInfluxDBClient):
        # Arrange
        mock_influx_client = MagicMock()
        mock_query_api = MagicMock()
        mock_data_frame = MagicMock()

        mock_influx_client.query_api.return_value = mock_query_api
        mock_query_api.query_data_frame.return_value = mock_data_frame
        MockInfluxDBClient.return_value.__enter__.return_value = mock_influx_client

        mock_data_frame.empty = False
        mock_data_frame.rename.return_value = mock_data_frame
        mock_data_frame.sort_values.return_value = mock_data_frame
        mock_data_frame.drop_duplicates.return_value = mock_data_frame  # you need to mock this method as well
        batch_list_dict = [{'batch_id': 'id1', 'time': '2023-01-01'}]
        mock_data_frame.get.return_value.to_dict.return_value = batch_list_dict

        # Act
        result = get_batch_ids()

        # Assert
        self.assertEqual(result, [{'batch_id': 'id1', 'time': '2023-01-01'}])
        mock_influx_client.query_api.assert_called_once()
        mock_query_api.query_data_frame.assert_called_once()
        mock_data_frame.rename.assert_called_once_with(columns={"_time": "time", '_measurement': "batch_id"})
        mock_data_frame.sort_values.assert_called_once_with(by=['time'], ascending=False)


class TestGetLastBatchID(TestCase):

    @patch('buerkert_app.utils.utils.get_batch_ids')
    def test_get_last_batch_id(self, mock_get_batch_ids):
        # Arrange
        mock_get_batch_ids.return_value = [{'batch_id': '10'}, {'batch_id': '20'}, {'batch_id': '30'}]

        # Act
        result = get_last_batch_id()

        # Assert
        self.assertEqual(result, 10)
