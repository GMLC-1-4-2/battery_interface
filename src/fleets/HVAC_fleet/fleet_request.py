# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 2018
For GMLC 1.4.2, 
Creating the Fleet Interface

@author: Jin Dong (ORNL), Teja Kuruganti (ORNL)
"""

from datetime import datetime, timedelta


class FleetRequest:
    """
    This class describes input fields required by fleets
    HVAC default discretization step is 10 mins
    """

    def __init__(self, ts = datetime.utcnow(), sim_step = timedelta(hours = 1/6), p = 0, q= 0, steps = 1, forecast = 0):
        """
        Constructor
        """

        # Timestamp in simulation loop: datetime
        self.StartTime = ts

        # Simulation time step: timedelta object
        self.Timestep = sim_step

        # Real power request
        self.P_request = p

        # Reactive power request
        self.Q_request = q
        
#        #Number of steps in simulation
        self.Steps = steps
        
        # NREL WaterHeater only: Number of steps in simulation.
        # This value is always = 1 for the sake of not changing WaterHeater code
#        self.steps = 1
        
        #Requesting a forecast Y/N
        self.Forecast = forecast
