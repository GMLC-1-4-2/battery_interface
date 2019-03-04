# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 10:43:27 2018

@author: cbooten
"""

from datetime import datetime


class WHResponse:
    """
    This class describes 1-timestep output of a water heater
    """

    def __init__(self, ts=datetime.utcnow()):
        """
        Constructor with default values
        """
        
        self.Ttank = 0
        self.Tset = 0 
        self.Eused = 0 
        self.PusedMax = 0
        self.Eloss = 0
        self.ElementOn = 0
        self.Eservice = 0
        self.SOC = 0
        self.AvailableCapacityAdd = 0
        self.AvailableCapacityShed = 0
        self.ServiceCallsAccepted = 0
        self.IsAvailableAdd = 0
        self.IsAvailableShed = 0
        
#        return Ttank_ts, Tset_ts,  Eused_ts,  PusedMax_ts, Eloss_ts,  Element_on_ts, Eservice_ts, SOC, Available_Capacity_Add, Available_Capacity_Shed, service_calls_accepted_ts, isAvailable_add_ts, isAvailable_shed_ts