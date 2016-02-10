#!/usr/bin/env python
import pyrow
import time
import requests
import thread
import os

POST_URL = "https://influxdb.paas.high.am/write?db=rowlog"
FIELDS = ['distance', 'spm', 'pace', 'calhr', 'power']

def add_data_point(records, data, force):
    field_values = ",".join(["{0}={1}".format(h, data[h]) for h in FIELDS])
    record = "performance,time={0} {1}".format(data['time'], field_values)
    print record

    records.append(record)

    if len(records) == 5:
		aggr_records = "\n".join(records)
        resp = requests.post(POST_URL, data=record, auth=('rowlogger', os.ENVIRON['ROWLOGGER_PASSWORD']), verify=False)
        print "POSTED! {0}".format(resp)

        records = []

if __name__ == "__main__":

    while True:

        # check for ergs until we find one
        ergs = []

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
        records = []

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

            thread.start_new_thread(add_data_point, (records, monitor, force))

            forcedata = ",".join([str(f) for f in force])

            #Get workout conditions
            workout = erg.get_workout()
