# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from datetime import datetime, timedelta


class FleetResponse:
    """
    This class describes 1-timestep output of a fleet
    """

    def __init__(self, ts=datetime.utcnow()):
        """
        Constructor with default values
        """
        # Are the ts and sim_step necessary?
        self.ts = ts                        # Start of current time period
        self.sim_step = timedelta(hours=3)  # Length of current time period (same as most recent request sim_step)

        # Results related to the most recent request
        self.P_togrid = None    # Previously called P_injected
        self.Q_togrid = None    # Previously called Q_injected
        self.P_service = None   # Dito
        self.Q_service = None   # Actual service being supplied in response to most recent request

        # Constraints for the next time period
        self.E              = None
        self.C              = None
        self.P_togrid_max   = None
        self.P_togrid_min   = None
        self.Q_togrid_max   = None
        self.Q_togrid_min   = None
        self.P_service_max  = None
        self.P_service_min  = None
        self.Q_service_max  = None
        self.Q_service_min  = None
        self.P_dot_up       = None
        self.P_dot_down     = None
        self.Q_dot_up       = None
        self.Q_dot_down     = None
        self.Eff_charge     = None
        self.Eff_discharge  = None
        self.dT_hold_limit  = None
        self.T_restore      = None
        self.Strike_price   = None
        self.SOC_cost       = None
