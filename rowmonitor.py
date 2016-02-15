#!/usr/bin/env python
import pyrow
import time
import requests
import thread
import os
import sys
import logging
import json
from usb.core import USBError

POST_URL = "https://influxdb.paas.high.am/write?db=rowlog"
FIELDS = ['distance', 'spm', 'pace', 'calhr', 'power']

global records
records = []

class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

def add_data_point(data, force, username, password):

    global records

    field_values = ",".join(["{0}={1}".format(h, data[h]) for h in FIELDS])
    record = "performance,time_elapsed={1} {2} {0}".format(int(time.time()*1000000000), data['time'], field_values)

    records.append(record)

    if len(records) == 5:
		aggr_records = "\n".join(records)
		resp = requests.post(POST_URL, data=aggr_records, auth=(username, password), verify=False)
		print "POSTED! {0}".format(resp)
		records = []

if __name__ == "__main__":

    config = json.loads(open(sys.argv[1], "r").read())
    home_dir = config["working_directory"]
    username = config["database"]["username"]
    password = config["database"]["password"]

    logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
       filename="{0}/rowmonitor.log".format(home_dir),
       filemode='a'
    )

    stdout_logger = logging.getLogger('STDOUT')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    print "Starting rowmonitor..."

    while True:

        # check for ergs until we find one
        ergs = []
        records = []
        erg = None

        while len(ergs) == 0:
            ergs = list(pyrow.find())
            time.sleep(5)

        # get the first erg in the list
        erg = pyrow.pyrow(ergs[0])

        print "Found an erg! {0}".format(erg)

        # loop until workout begins
        workout = erg.get_workout()

        while workout['state'] == 0:
            time.sleep(1)
            workout = erg.get_workout()

        print "Starting workout {0}".format(workout)

        # loop until workout ends
        while workout['state'] == 1:

            forceplot = erg.get_force_plot()

            #Loop while waiting for drive
            while forceplot['strokestate'] != 2 and workout['state'] == 1:

                #ToDo: sleep?
                forceplot = erg.get_force_plot()
                workout = erg.get_workout()

            #Record force data during the drive
            force = forceplot['forceplot'] #start of pull (when strokestate first changed to 2)
            monitor = erg.get_monitor() #get monitor data for start of stroke

            #Loop during drive
            while forceplot['strokestate'] == 2:

                #ToDo: sleep?
                forceplot = erg.get_force_plot()
                force.extend(forceplot['forceplot'])

            forceplot = erg.get_force_plot()
            force.extend(forceplot['forceplot'])

            thread.start_new_thread(add_data_point, (monitor, force, username, password))

            forcedata = ",".join([str(f) for f in force])

            #Get workout conditions
            workout = erg.get_workout()

        erg.release()
