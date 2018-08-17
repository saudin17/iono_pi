#!/usr/bin/python3
# pylint: disable=locally-disabled, broad-except, line-too-long
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#  Desc : Main script to collect data and set IO using IonoPi
#  File : pydas.py
# ----------------------------------------------------------------------
""" Main script
"""
import os
import logging
import logging.handlers
import platform
import time
from datetime import datetime
import threading
# custom
from functions import create_log, clear_screen, unix_time
from iono_wrapper import IonoWrapper

def polling(module, config):
    """ polling """
    logging.debug("Function polling")
    while True:

        # check for mean
        now = datetime.now()

        # get the total seconds
        ptime = unix_time(now)

        # check for new mean
        if int(ptime / config['store_time']) == (ptime / config['store_time']):
            # new mean
            logging.info("*** New mean ***")

            # store values to csv file
            module.store_ced_data_csv()

        # check for new polling
        if int(ptime / config['polling_time']) == (ptime / config['polling_time']):

            # new polling
            logging.info("--- New polling ---")

            # switch led on
            module.set_led_status(True)
            module.set_relay_status(1, True)
            module.set_open_collector_status(1, True)

            # polling
            module.get_digital_input()
            module.get_analog_input()
            module.get_relay_output()
            module.get_open_collector_output()
            module.get_one_wire_input()

            # store values to csv file
            module.store_data_csv()

            # append new temperature data
            # to make later mean on store_time
            module.append_temperature()

            # wait to avoid more calls
            time.sleep(1.5)
            # switch led off
            module.set_led_status(False)
            module.set_relay_status(1, False)
            module.set_open_collector_status(1, False)

            # reset digital inputs events status
            module.reset_digital_input_events()

        # sleep
        time.sleep(0.1)

def main():
    """ Main function """
    module = None
    try:

        # config
        config = {
            'polling_time' : 10,    # polling (seconds)
            'store_time' : 60,      # store data (seconds)
            'data_path' : None,     # data path
            'ftp_path' : None,      # data path for ftp export
            'file_header' : 'iono', # data file header
        }

        # iono config
        config_iono = {
            'use_ai' : True, # analog input
            'use_io' : True, # digital io
            'use_ev' : True, # digital io events
            'use_1w' : True, # one wire input (temperature)
            'use_ro' : True, # relay outputs
            'use_oc' : True, # open collectors
            'use_ld' : True, # on board led
        }

        # Clear
        clear_screen()

        # Logging debug | DEBUG INFO
        create_log(logging.DEBUG)

        # Start
        now = datetime.now()
        logging.info("Program start @ %s on %s", now.strftime("%Y-%m-%d %H:%M:%S"), platform.system())

        # path
        data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        config['data_path'] = data_path

        ftp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ftp')
        if not os.path.exists(ftp_path):
            os.mkdir(ftp_path)
        config['ftp_path'] = ftp_path

        # create main module object
        logging.info("Creating main iono object...")
        module = IonoWrapper(config, config_iono)

        # start main loop
        logging.info("Starting main thread")
        main_thread = threading.Thread(target=polling, daemon=True, args=[module, config])
        main_thread.start()

        # loop forever waiting for user ctrl+c to exit
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logging.critical("An exception was encountered in main(): %s", str(ex))
    finally:
        module.cleanup()
        logging.info("End")

if __name__ == '__main__':
    main()
