#!/usr/bin/python3
# pylint: disable=broad-except, line-too-long
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#  Desc : Iono Pi Custom Wrapper Class
#  File : iono.py
# ----------------------------------------------------------------------
""" Arpa Vda Custom Class
"""
import sys
import os
import logging
import logging.config
from datetime import datetime
from math import sqrt
from iono import Iono

if __name__ == '__main__':
    sys.exit(1)

class IonoWrapper(Iono):
    """ Arpa iono main class """
    def __init__(self, config, config_iono):
        super().__init__(config_iono)

        # set properties
        self.config = config

        # temperature stuff
        self.decimals = 2
        self.data_temperature = []
        self.one_wire_inputs[0]['db_id'] = 1 # set database id

    def _mean(self, lst):
        """ Calculate mean """
        logging.debug("Calculating mean")
        if not lst:
            return float(None)

        return float(sum(lst)) / len(lst)

    def _stddev(self, lst):
        """ Calculate standard deviation """
        logging.debug("Calculating standard deviation")
        data_mean = self._mean(lst)
        data_sum = 0

        for item in lst:
            data_sum += pow(item - data_mean, 2)

        return sqrt(float(data_sum) / (len(lst) - 1))

    def append_temperature(self):
        """ Store new data into array """
        logging.debug("Function append_temperature")

        # get item
        # ain = self.analog_inputs[0]
        # if ain and ain['value']:
        #     # calculate temp in °C
        #     # 0÷10 Vdc 0÷50°C
        #     temp = float(ain['value']) * 5
        #     logging.debug("Appending %s to temperature list", temp)
        #     # append data
        #     self.data_temperature.append(temp)
        #     logging.debug(self.data_temperature)

        # get item
        owi = self.one_wire_inputs[0]
        if owi and owi['value']:
            # append data
            logging.debug("Appending %s to temperature list", owi['value'])
            self.data_temperature.append(float(owi['value']))
            logging.debug(self.data_temperature)

    def store_data_csv(self):
        """ Store all collected data to csv file """
        logging.debug("Function store_data_csv")

        try:

            # date time
            now = datetime.now()

            # empty row
            row = ''
            date_time = now.strftime('%Y-%m-%d %H:%M:%S') # datetime

            logging.debug("Looping through digital inputs")
            row += "# digital inputs\n"
            for din in self.digital_inputs:
                logging.debug("Measure %s, id %s", din['name'], din['id'])

                # build row
                row += date_time + "\t"
                row += str(din['id']) + "\t" # id for database
                row += str(din['status']) + "\t" # channel status 1|0
                row += str(din['status_ev']) + "\t" # event status 1|0
                row += str(din['name']) + "\n" # channel name

            logging.debug("Looping through analog inputs")
            row += "# analog inputs\n"
            for ain in self.analog_inputs:
                logging.debug("Measure %s, id %s", ain['name'], ain['id'])

                # build row
                row += date_time + "\t"
                row += str(ain['id']) + "\t" # id
                if ain['value']:
                    row += str(round(ain['value'], 2)) + "\t" # channel values in volts
                else:
                    row += str(None) + "\t"
                row += str(ain['name']) + "\n" # channel name

            logging.debug("Looping through relay outputs")
            row += "# relay outputs\n"
            for rel in self.relay_outputs:
                logging.debug("Measure %s, id %s", rel['name'], rel['id'])

                # build row
                row += date_time + "\t"
                row += str(rel['id']) + "\t" # measure id for database
                row += str(rel['status']) + "\t" # channel status 1|0
                row += str(rel['name']) + "\n" # channel name

            logging.debug("Looping through open collector outputs")
            row += "# open collector outputs\n"
            for opc in self.open_collector_outputs:
                logging.debug("Measure %s, id %s", opc['name'], opc['id'])

                # build row
                row += date_time + "\t"
                row += str(opc['id']) + "\t" # measure id for database
                row += str(opc['status']) + "\t" # channel status 1|0
                row += str(opc['name']) + "\n" # channel name

            logging.debug("Looping through 1wire inputs")
            row += "# 1wire inputs\n"
            for owi in self.one_wire_inputs:
                logging.debug("Measure %s, id %s", owi['name'], owi['id'])

                # build row
                row += date_time + "\t"
                row += str(owi['id']) + "\t" # measure id for database
                if owi['value']:
                    row += str(round(owi['value'], 2)) + "\t" # channel value
                else:
                    row += str(None) + "\t"
                row += str(owi['name']) + "\n" # channel name

            # build daily file_name
            file_name = os.path.join(
                self.config['data_path'],
                self.config['file_header']+"_"+now.strftime('%Y-%m-%d')+".dat"
            ) # .%H%M

            # dump data to file
            logging.info("Saving data to file %s...", file_name)
            logging.debug("File row\n%s", row)
            with open(file_name, "a") as file:
                file.write(row)

            return True

        except Exception as ex:
            logging.error("An exception was encountered in store_data_csv: %s", str(ex))
            return False

    def store_ced_data_csv(self):
        """ Store 1 wire collected data to csv file for ced """
        logging.debug("Function store_ced_data_csv")

        try:
            if not self.data_temperature:
                logging.warning("No data found, data array is empty!")
                return False

            # get item
            logging.debug("Get 1wire first item")
            #item = self.analog_inputs[0]
            item = self.one_wire_inputs[0]
            if item is None:
                logging.warning("No item found!")
                return False
            # get database id
            dbid = item['db_id']

            # build row
            logging.debug("Build record")
            # date time
            now = datetime.now()
            row = now.strftime('%Y-%m-%d %H:%M:00') + "\t"
            # measure id for database
            row += str(dbid) + "\t"
            # average
            row += str(round(float(self._mean(self.data_temperature)), self.decimals)) + "\t"
            # min
            row += str(round(float(min(self.data_temperature)), self.decimals)) + "\t"
            # max
            row += str(round(float(max(self.data_temperature)), self.decimals)) + "\t"
            # stddev
            row += str(round(float(self._stddev(self.data_temperature)), self.decimals)) + "\n"

            # build daily file_name
            file_name = os.path.join(
                self.config['ftp_path'],
                self.config['file_header']+"_"+now.strftime('%Y-%m-%d')+".dat"
            ) # .%H%M

            # dump data to file
            logging.info("Saving data to file %s...", file_name)
            logging.debug("File row\n%s", row)
            with open(file_name, "a") as file:
                file.write(row)

            return True

        except Exception as ex:
            logging.error("An exception was encountered in store_ced_data_csv: %s", str(ex))
            return False

        finally:
            # reset array
            logging.info("Reset data array")
            self.data_temperature = []

    def parse_event(self, din):
        """ Parse event """
        # custom function for subclass to override
        logging.info("Function parse_event")

        try:

            # get status (on/off)
            logging.debug("GPIO %s, id %s, status %s",
                          din['name'], din['id'], din['status_ev'])


            # send telegram, mail


            # store event
            self.store_event(din)

        except Exception as ex:
            logging.error("An exception was encountered in parse_event: %s", str(ex))

    def store_event(self, din):
        """ Store digital input event to file """
        logging.info("Function store_event")
        try:
            logging.debug("Digital input %s", din)

            if not din is None:

                now = datetime.now()
                # one hour back for timestamp
                #now = now - timedelta(hours=1)

                # empty row
                row = ''

                # build row
                row += now.strftime('%Y-%m-%d %H:%M:%S.%f') + "\t"
                row += str(din['id']) + "\t" # measure id for database
                row += str(din['status_ev']) + "\t" # channel status 1|0
                row += str(din['name']) + "\n" # channel name

                # build file_name
                logging.debug("Build file name")
                file_name = os.path.join(
                    self.config['data_path'],
                    self.config['file_header']+"_events_"+now.strftime('%Y-%m-%d')+".dat"
                )

                # dump data to file
                logging.debug("Saving data to file %s...", file_name)
                logging.debug("File row [%s]", row)
                with open(file_name, "a") as file:
                    file.write(row)

        except Exception as ex:
            logging.error("An exception was encountered in store_event: %s", str(ex))
