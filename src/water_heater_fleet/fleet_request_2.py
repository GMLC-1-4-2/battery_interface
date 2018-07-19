# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from datetime import datetime, timedelta


class FleetRequest:
    """
    This class describes input fields required by fleets
    """

    def __init__(self, ts = datetime.utcnow(), sim_step = timedelta(hours = 1), p= 0, q= 0, steps = 1, forecast = 0):
        """
        Constructor
        """

        # Timestamp in simulation loop: datetime
        self.StartTime = ts

        # Simulation time step: timedelta object
        self.Timestep = sim_step

        # Real power request
        self.P_request = 0#p

        # Reactive power request
        self.Q_request = q
        
        #Number of steps in simulation
        self.Steps = steps
        
        #Requesting a forecast Y/N
        self.Forecast = forecast
