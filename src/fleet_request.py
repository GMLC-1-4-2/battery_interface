# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from datetime import datetime, timedelta


class FleetRequest:
    """
    This class describes input fields required by fleets 
    """
    def __init__(self, ts=datetime.utcnow(),
                 sim_step=timedelta(hours=1),
                 start_time=None,
                 p=None, q=None, steps=1):
        """
        Constructor
        """
        # Timestamp in simulation loop: datetime
        self.ts_req = ts
        
        # Timestamp in simulation loop: datetime
        self.start_time = start_time

        # Simulation time step: timedelta object
        self.sim_step = sim_step

        # Real power request
        self.P_req = p

        # Reactive power request
        self.Q_req = q

        # NREL WaterHeater only: Number of steps in simulation.
        # This value is always = 1 for the sake of not changing WaterHeater code
        self.steps = 1
