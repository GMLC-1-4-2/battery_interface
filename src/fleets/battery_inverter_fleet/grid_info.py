# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}
# This program inports a day of generic, normalized frequency and voltage data and makes it avalible on request to calling functions

from __future__ import absolute_import
import numpy as np
from datetime import datetime
import csv


class GridInfo:
    """
    This class provides common info about the grid
    """
    def __init__(self, ConfigFile, **kwargs):
        
        f_base = 60#Hz
        v_base = 240#V
        n = 86400
        self.time = np.zeros(n)
        # these variables hold the frequency and voltage data for each location
        self.frequency = np.zeros((n,2))
        self.voltage = np.zeros((n,2))

        i = 0
        with open(ConfigFile) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                self.time[i] = float(row[0])
                self.frequency[i,0] = float(row[1])*f_base
                self.frequency[i,1] = float(row[2])*f_base
                self.voltage[i,0] = float(row[3])*v_base
                self.voltage[i,1] = float(row[4])*v_base
                i += 1

    def get_voltage(self, ts=datetime.utcnow(), location=0):
        TS = float(ts.hour/1.0+ts.minute/60+ts.second/3600)
        """ idx = (np.abs(self.time - TS)).argmin() """
        idx = np.searchsorted(self.time, TS, side="left")
        return self.voltage[idx-1,location]

    def get_frequency(self, ts=datetime.utcnow(), location=0):
        TS = float(ts.hour/1.0+ts.minute/60+ts.second/3600)
        """ idx = (np.abs(self.time - TS)).argmin()     """
        idx = np.searchsorted(self.time, TS, side="left") 
        return self.frequency[idx-1,location]