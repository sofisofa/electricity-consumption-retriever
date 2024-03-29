#!/usr/bin/env python3

import datetime as dt
import logging
import pytz
import json
import os

from EdistribucionAPI import Edistribucion
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    filename=f'{os.getcwd()}/electricityconsumption.log',
                    filemode='w')


logger = logging.getLogger(__name__)

load_dotenv()

USERNAME = os.getenv('EN_USER')
PW = os.getenv('EN_PASS')


class Endesa:
    
    def __init__(self, user, pw):
        logger.info("Loging in Endesa")
        self.edis = Edistribucion(user, pw)
        
    def get_last_invoiced_consumption_data(self):
        logger.info("Retrieving last invoiced data from Endesa")
        l_cups = self.edis.get_list_cups()[-1]
        l_cups_id = l_cups['Id']
        cycles = self.edis.get_list_cycles(l_cups_id)
        meas = self.edis.get_meas(l_cups_id, cycles[0])
        consumption_data = []
        
        for day in meas:
            day_in_data = []
            for hourly_point in day:
                day_in_data.append(
                    {'date': hourly_point['date'],
                     'hour': hourly_point['hourCCH'],
                     'label': hourly_point['hour'],
                     'consumption': hourly_point['valueDouble']
                     }
                )
            consumption_data.append(day_in_data)
        
        return consumption_data
    
    def get_interval_consumption_data(self, start_date, end_date):
        logger.info(f"Retrieving consumption data in from Endesa. Time period: {start_date} to {end_date}")
        l_cups = self.edis.get_list_cups()[-1]
        l_cups_id = l_cups['Id']
        meas = self.edis.get_meas_interval(l_cups_id, start_date, end_date)
        consumption_data = []
        
        for day in meas:
            day_in_data = []
            for hourly_point in day:
                if hourly_point['obtainingMethod'] != 'E' and 'valueDouble' in hourly_point.keys():
                    day_in_data.append(
                        {'date': hourly_point['date'],
                         'hour': hourly_point['hourCCH'],
                         'label': hourly_point['hour'],
                         'consumption': hourly_point['valueDouble']
                         }
                    )
            if len(day_in_data) > 0:
                consumption_data.append(day_in_data)
        
        return consumption_data

    @staticmethod
    def convert_to_utc(data_dt):
        local = pytz.timezone("Europe/Madrid")
        naive = dt.datetime.strptime(data_dt, "%d/%m/%Y %H:%M:%S")
        local_dt = local.localize(naive)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt
    
    @staticmethod
    def reformat_data(data):
        new_data = []
        for day in data:
            new_day = []
            for point in day:
                new_point = {}
                raw_date = point['date']
                raw_hour = point['hour']
                if raw_hour < 10:
                    raw_dt = raw_date + f" 0{raw_hour-1}:00:00"
                else:
                    raw_dt = raw_date + f" {raw_hour-1}:00:00"
                new_dt = Endesa.convert_to_utc(raw_dt)
                new_point['datetime'] = new_dt.isoformat()
                new_point['consumption'] = point['consumption']
                new_day.append(new_point)
            new_data.append(new_day)
        return new_data
    
        
def run():
    endesa = Endesa(USERNAME, PW)
    consumption_data = endesa.get_last_invoiced_consumption_data()
    consumption_data_reform = endesa.reformat_data(consumption_data)
    
    # Get year and month of consumption data
    datetime = dt.datetime.fromisoformat(consumption_data_reform[0][0]["datetime"])
    month = datetime.strftime("%b")
    year = datetime.strftime("%y")
    #
    consumption_json = {'creation date': dt.date.isoformat(dt.date.today()),
                        'hourly_consumption': consumption_data}

    logger.info("Dumping Endesa data into JSON")
    with open(f"{os.getenv('PATH_TO_CONSUMPTION_FILES')}en_consumption_{month}_{year}.json", 'w+') as f_obj:
        json.dump(consumption_json, f_obj)


if __name__ == "__main__":
    run()
