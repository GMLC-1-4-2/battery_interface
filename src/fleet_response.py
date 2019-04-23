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
        self.sim_step = None  # Length of current time period (same as most recent request sim_step)

        # Results related to the most recent request (all in units of kW or kvar, average over the recent timestep)
        self.P_togrid = None    # Previously called P_injected
        self.Q_togrid = None    # Previously called Q_injected
        self.P_service = None   # Dito
        self.Q_service = None   # Actual service being supplied in response to most recent request
        self.P_base = None      # Baseline active power
        self.Q_base = None      # Baseline reactive power

        # Constraints for the next time period

        # Available Energy stored at the end of the most recent timestep (kWh)
        self.E              = None

        # Potential energy capacity stored (prior to conversion to AC) when the state of charge (SoC) changes
        # from 100% to 0% for the next timestep (kWh)
        self.C              = None

        # Maximum and minimum power from device to grid, for the next timestep (can be zero, loads are negative)
        # (kW, average over next timestep)
        self.P_togrid_max   = None
        self.P_togrid_min   = None

        # Maximum and minimum reactive power to grid, for the next timestep (can be zero, loads negative)
        # (kvar, average over next timestep)
        self.Q_togrid_max   = None
        self.Q_togrid_min   = None

        # Maximum and minimum power deliverable for grid services for the next timestep.  This is the
        # difference between P_togrid_* and the baseline P_togrid (i.e., what the fleet would be doing
        # were it not asked to provide service). (kW, average over next timestep)
        # Ditto for the reactive power max/min.  (kvar, average over next timestep)
        self.P_service_max  = None
        self.P_service_min  = None
        self.Q_service_max  = None
        self.Q_service_min  = None

        # Ramp rate, power up/down:  the maximum rate of increase (*_up) or decrease (*_down) of power output
        # to the grid for the next timestep (kW/sec or kvar/sec)
        self.P_dot_up       = None
        self.P_dot_down     = None
        self.Q_dot_up       = None
        self.Q_dot_down     = None

        # Charging efficiency:  Fraction of the energy supplied to the converter that is stored at power grid
        # requested (or at minimum power to grid if power requested = None) (percent)
        self.Eff_charge     = None

        # Discharging efficiency:  Fraction of the energy generated or drawn from storage that is transformed to useful
        # form by the converter at power grid requested (or at maximum power to grid if power requested = None)
        # (percent)
        self.Eff_discharge  = None

        # Time limit, hold:  Maximum duration of "hold state" for SoC at other than desired condition (hours)
        self.dT_hold_limit  = None

        # Time, restoration:  Time of day at which the desired SoC condition must be restored (hour of day)
        self.T_restore      = None

        # Strike price:  Energy price/incentive threshold at which device initiates response ($/kWh)
        self.Strike_price   = None

        # State-of-charge cost:  Incentive requirement for device to be at SoC other than 100% ($/hr)
        self.SOC_cost       = None
