# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from datetime import datetime, timedelta


class FleetRequest:
    """
    This class describes input fields required by fleets 
    """
# why is the above comment exactly the same as that one in fleet_config.py ??
	
    def __init__(self, ts=datetime.utcnow(), sim_step=timedelta(hours=1), p=None, q=None):
        """
        Constructor
        """
        # Timestamp in simulation loop: datetime
        self.ts_req = ts

        # Simulation time step: timedelta object
        self.sim_step = sim_step

        # Real power request
        self.P_req = p

        # Reactive power request
        self.Q_req = q
