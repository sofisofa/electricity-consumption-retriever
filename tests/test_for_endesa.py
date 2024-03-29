#!/usr/bin/env python3

import pytest
import os
from dotenv import load_dotenv
import datetime as dt
import pytz
from unittest.mock import MagicMock, patch
from src.electricity_consumption import endesa_api as ea
from src.electricity_consumption.endesa_api import Endesa

EN_USER = 'EN_USER'
EN_PW = 'EN_PASS'
LOGIN_URL = 'https://core.holaluz.com/api/private/login_check'
CONSUMPTION_URL = 'https://zc-consumption.holaluz.com/consumption'

L_CUPS = {'Id': 'Id'}
CYCLES = ['last cycle']
MEASURED_INVOICED_CONSUMPTION = [[
    {'date': '08/03/2023',
     'hourCCH': 1,
     'hour': '00 - 01 h',
     'invoiced': True,
     'typePM': '5',
     'valueDouble': 0.922,
     'obtainingMethod': 'R',
     'real': True,
     'value': '0,922'
     },
    {'date': '08/03/2023',
     'hourCCH': 2,
     'hour': '01 - 02 h',
     'invoiced': True,
     'typePM': '5',
     'valueDouble': 0.539,
     'obtainingMethod': 'R',
     'real': True,
     'value': '0,539'
     }
]]

MEASURED_INTERVAL_CONSUMPTION = [
    [
        {'date': '08/03/2023',
         'hourCCH': 1,
         'hour': '00 - 01 h',
         'invoiced': True,
         'typePM': '5',
         'valueDouble': 0.922,
         'obtainingMethod': 'R',
         'real': True,
         'value': '0,922'
         },
        {'date': '08/03/2023',
         'hourCCH': 2,
         'hour': '01 - 02 h',
         'invoiced': True,
         'typePM': '5',
         'valueDouble': 0.539,
         'obtainingMethod': 'R',
         'real': True,
         'value': '0,539'
         }
    ],
    [
        {'date': '09/03/2023',
         'hourCCH': 1,
         'hour': '00 - 01 h',
         'invoiced': True,
         'typePM': '5',
         'valueDouble': 0.922,
         'obtainingMethod': 'E',
         'real': True,
         'value': '0,922'
         },
        {'date': '09/03/2023',
         'hourCCH': 2,
         'hour': '01 - 02 h',
         'invoiced': True,
         'typePM': '5',
         'valueDouble': 0.539,
         'obtainingMethod': 'E',
         'real': True,
         'value': '0,539'
         }
    ]
]

EXPECTED_CONSUMPTION_DATA = [[
    {'date': '08/03/2023',
     'hour': 1,
     'label': '00 - 01 h',
     'consumption': 0.922
     },
    {'date': '08/03/2023',
     'hour': 2,
     'label': '01 - 02 h',
     'consumption': 0.539,
     }
    
]]

EXPECTED_REFORMAT_DATA = [[
    {'datetime': '2023-03-07T23:00:00+00:00', 'consumption': 0.922},
    {'datetime': '2023-03-08T00:00:00+00:00', 'consumption': 0.539}
]]


class TestClassUpdateDatabase:
    @patch("src.electricity_consumption.endesa_api.Edistribucion")
    def test_get_last_invoiced_consumption_data(self, mock):
        Endesa.edis = mock.return_value
        Endesa.edis.get_list_cups.return_value = [L_CUPS]
        Endesa.edis.get_list_cycles.return_value = CYCLES
        Endesa.edis.get_meas.return_value = MEASURED_INVOICED_CONSUMPTION
        
        #When
        en = ea.Endesa(EN_USER, EN_PW)
        
        #Then
        data = en.get_last_invoiced_consumption_data()
        Endesa.edis.get_list_cycles.assert_called_with('Id')
        Endesa.edis.get_meas.assert_called_with(L_CUPS['Id'], CYCLES[0])
        assert data == EXPECTED_CONSUMPTION_DATA
        
    @patch("src.electricity_consumption.endesa_api.Edistribucion")
    def test_get_interval_consumption_data(self, mock):
        Endesa.edis = mock.return_value
        Endesa.edis.get_list_cups.return_value = [L_CUPS]
        Endesa.edis.get_meas_interval.return_value = MEASURED_INTERVAL_CONSUMPTION
        
        en = ea.Endesa(EN_USER, EN_PW)
        
        # Then
        data = en.get_interval_consumption_data('2023-03-08', '2023-03-09')
        Endesa.edis.get_meas_interval.assert_called_with(L_CUPS['Id'], '2023-03-08', '2023-03-09')
        assert data == EXPECTED_CONSUMPTION_DATA

    def test_convert_to_utc(self):
        expected_utc = dt.datetime(2023, 3, 8, 0, 0, tzinfo=pytz.utc)
        raw_dt = EXPECTED_CONSUMPTION_DATA[0][0]['date'] + f" 0{EXPECTED_CONSUMPTION_DATA[0][0]['hour']}:00:00"
        data = Endesa.convert_to_utc(raw_dt)
        assert data == expected_utc

    def test_reformat_data(self):
        data = Endesa.reformat_data(EXPECTED_CONSUMPTION_DATA)
        assert data == EXPECTED_REFORMAT_DATA

    @patch("src.electricity_consumption.endesa_api.Edistribucion")
    @patch("src.electricity_consumption.endesa_api.json.dump")
    @patch("builtins.open")
    def test_run_opens_file_and_calls_json_dump(self, mock_open, mock_dump, mock_edis):
        Endesa.edis = mock_edis.return_value
        Endesa.edis.get_list_cups.return_value = [L_CUPS]
        Endesa.edis.get_list_cycles.return_value = CYCLES
        Endesa.edis.get_meas.return_value = MEASURED_INVOICED_CONSUMPTION

        date = dt.datetime.fromisoformat(EXPECTED_REFORMAT_DATA[0][0]["datetime"])
        month = date.strftime("%b")
        year = date.strftime("%y")

        dummy_obj = MagicMock()
        dummy_obj.__enter__.return_value = dummy_obj
        dummy_obj.__exit__.return_value = None
        mock_open.return_value = dummy_obj
        consumption_json = {'creation date': dt.date.isoformat(dt.date.today()),
                            'hourly_consumption': EXPECTED_CONSUMPTION_DATA}
        
        load_dotenv()
        ea.run()
        mock_open.assert_called_with(f"{os.getenv('PATH_TO_CONSUMPTION_FILES')}en_consumption_{month}_{year}.json", 'w+')
        mock_dump.assert_called_with(consumption_json, dummy_obj)


if __name__ == "__main__":
    pytest.main([__file__])
