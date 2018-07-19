# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 10:43:27 2018

@author: cbooten
"""

from datetime import datetime


class WHFleetResponse:
    """
    This class describes 1-timestep output of a water heater
    """

    def __init__(self, numWH = 1, Steps = 1, ts=datetime.utcnow(),):
        """
        Constructor with default values
        """
        
        self.Tset = [[0 for x in range(Steps)] for y in range(numWH)]
        self.Ttank = [[0 for x in range(Steps)] for y in range(numWH)]
        self.dTtank_set = [[0 for x in range(Steps)] for y in range(numWH)]
        self.SoC = [[0 for x in range(Steps)] for y in range(numWH)]
        self.AvailableCapacityAdd = [[0 for x in range(Steps)] for y in range(numWH)]
        self.AvailableCapacityShed = [[0 for x in range(Steps)] for y in range(numWH)]
        self.ServiceCallsAccepted = [[0 for x in range(Steps)] for y in range(numWH)]
        self.ServiceProvided = [[0 for x in range(Steps)] for y in range(numWH)]
        self.IsAvailableAdd = [[0 for x in range(Steps)] for y in range(numWH)]
        self.IsAvailableShed = [[0 for x in range(Steps)] for y in range(numWH)]
        self.elementOn = [[0 for x in range(Steps)] for y in range(numWH)]
        self.TotalServiceProvidedPerTimeStep = [0 for y in range(Steps)]
        self.P_injected = [0 for y in range(Steps)]
        self.P_injected_max = [0 for y in range(Steps)]
        self.eta_charge = [0 for y in range(Steps)]
        self.eta_discharge = [0 for y in range(Steps)]
         
