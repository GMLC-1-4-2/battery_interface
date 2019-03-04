# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}
# This program inports a day of generic, normalized frequency and voltage data and makes it avalible on request to calling functions

from __future__ import absolute_import
import numpy as np
from datetime import datetime
import csv
import os
from dateutil import parser


class GridInfo:
    """
    This class provides common info about the grid
    """

    def __init__(self, input_file='Grid_Info_data_artificial_inertia.csv', **kwargs):
        # f_base = 60  # Hz
        # v_base = 240  # V
        n = 4501
        self.time = np.zeros(n)
        # these variables hold the frequency data for each location
        self.frequency = np.zeros((n, 2))
        self.voltage = np.zeros((n, 2))

        i = 0
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', input_file)
        with open(full_path) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if i == 0:
                    i += 1
                    continue
                else:
                    self.time[i] = float(row[0])
                    self.frequency[i, 0] = float(row[3])
                    self.frequency[i, 1] = float(row[10])
                    self.voltage[i, 0] = float(row[1])
                    self.voltage[i, 1] = float(row[8])
                    i += 1
                if i > n-1:
                    break

    def get_frequency(self, tcur=datetime.utcnow(), location=0, tstart=None):
        # Tst indicates the service start time.
        # Tcur is current time.
        # Note: artificial grid services usually lasts for up to 150 seconds
        if tstart is None:
            tstart = datetime(tcur.year, tcur.month, tcur.day, 0, 0, 0)
        Trelative = (tcur - tstart).total_seconds()

        if Trelative > self.time[-1]:
            raise ValueError('Exceeded the end of time for artificial inertia service.')

        idx = np.searchsorted(self.time, Trelative, side="left")
        return self.frequency[idx - 1, location]

    def get_voltage(self, tcur=datetime.utcnow(), location=0, tstart=None):
        # Tst indicates the service start time.
        # Tcur is current time.
        # Note: artificial grid services usually lasts for up to 150 seconds
        if tstart is None:
            tstart = datetime(tcur.year, tcur.month, tcur.day, 0, 0, 0)
        Trelative = (tcur - tstart).total_seconds()

        if Trelative > self.time[-1]:
            raise ValueError('Exceeded the end of time for specific grid service.')

        idx = np.searchsorted(self.time, Trelative, side="left")
        return self.voltage[idx - 1, location]

if __name__ == '__main__':
    from dateutil import parser
    from datetime import datetime, timedelta

    gi = GridInfo()
    # pickfreq = gi.get_frequency(parser.parse('2018-10-12 00:00:00'), parser.parse('2018-10-12 00:00:01'), 0)
    # print(pickfreq)

    start_time = parser.parse("2018-10-15 00:00:00")
    delt = timedelta(seconds=2/60)

    print(gi.get_frequency(start_time + delt, tstart=start_time))

    print(gi.get_frequency(start_time + 3*delt))

    print(gi.get_frequency(start_time + 100*delt))

    print(gi.get_voltage(start_time + 3 * delt))
