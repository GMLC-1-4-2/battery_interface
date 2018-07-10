# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from dateutil import parser
from datetime import datetime, timedelta
import calendar

from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse
from fleet_config import FleetConfig

from fleets.home_ac_fleet.home_ac_fleet import HomeAcFleet
from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet

import numpy as np
import pandas as pd


class PeakManagementService():
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """

    def __init__(self,
                 fleet=None,
                 capacity_scaling_factor=1.0,                       # To match drive cycle to fleet capacity
                 drive_cycle_file="drive.cycle.summer.peaky.csv",   # Data frame
                 f_reduction=0.1,                                   # Try to reduce annual peak by this amount
                 *args, **kwargs):

        self.drive_cycle_file = drive_cycle_file
        self.f_reduction = f_reduction

        # Establish a default simulation timestep (will always be 1-hour as far as I know)...
        self.sim_step = timedelta(hours=1)

        # Set the appropriate fleet to use.
        # Q:  What's the best way to pass in the fleet to instantiate?  Should the fleet be
        # instantiated in main and passed in as an object?
        if fleet == None:
            self.fleet = BatteryInverterFleet()
        elif fleet = "HomeAcFleet":
            self.fleet = HomeAcFleet()
        else:
            self.fleet = None   # Need to throw an exception here...

        # Set up the fleet (if necessary?)  Again, should this happen in main before fleet is passed in??
        fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=None)
        self.fleet.change_config(fleet_config)

        # Long term, we don't want a drive cycle, we want to call some kind of daily
        # load forecast service that a higher-level function in the software provides.
        # But for now, our whole purpose is testing...
        #
        # This data frame has columns (year, month_abbr, day, hour, load_forecast_mw), where month is
        # the three-letter month abbreviation (Jan, Feb, etc.) and all others are numeric...
        self.drive_cycle = pd.read_csv(self.drive_cycle_file)

        # There may be more straightforward ways to do this...just want to add a datetime object
        # matching the drive cycle's year, month_abbr, day, hour info...
        self.drive_cycle["month_num"] = [
                list(calendar.month_abbr).index(self.drive_cycle[abb]) for abb in self.drive_cycle["month"]
            ]
        self.drive_cycle["dt"] = [
                datetime.datetime(
                    self.drive_cycle["year"], self.drive_cycle["month_num"], self.drive_cycle["day"],
                    self.drive_cycle["hour"], 0, 0) ]

        # Ideally the fleet could tell us its capacity and we compute the scaling_factor from that
        # and the maximum value in the drive cycle...
        self.capacity_scaling_factor = capacity_scaling_factor
        self.drive_cycle.load_forecast_mw /= capacity_scaling_factor

        # Find the "annual" peak (largest peak in our drive cycle really) and the desired new peak...
        self.annual_peak = max(self.drive_cycle.load_forecast_mw)
        self.mw_target = self.annual_peak * (1 - self.f_reduction)

        # TODO:  Initialize something to hold stats



    def run_fleet_forecast_test(self):
        ndx_start = 0
        ndx_end = ndx_start + 23
        while ndx_end < len(self.drive_cycle.dt):   # Loop over days...
            dt_day = self.drive_cycle.dt[ndx_start:ndx_end]
            mw_day = self.drive_cycle.load_forecast_mw[ndx_start:ndx_end]
            p_needed = [self.no_neg(mw_day[i] - self.mw_target) for i in range(24)]

            ndx_start += 24
            ndx_end += 24

            # No need to work on days without high peaks
            if max(mw_day) <= self.mw_target:
                continue

            # Get a 24-hour forecast from fleet
            requests = []
            for i in [range(24)]:
                requests.append(FleetRequest(ts=dt_day[i], sim_step=self.sim_step, p=p_needed[i]))
            forecast_response = self.fleet.forecast(requests)

            # See if the forecast can meet the desired load
            deficit = [forecast_response[i].P_service - p_needed[i] for i in [range(24)]]
            insufficient = [deficit[i] < 0 for i in range(24)]
            if any(insufficient):
                # TODO:  NEED TO LOOP BACK AND REBUILD requests until we have a 24-hour request we know can be met

            # Now we know what the fleet can do, so ask it to do it

            for i in range(24):
                fleet_request = FleetRequest(ts=dt_day[i], sim_step=self.sim_step, p=forecast_response[i].P_service)
                fleet_response = self.fleet.process_request(fleet_request)
                # TODO:  store performance stats


    def no_neg(self, values):
        for i in range(values):
            if values[i] < 0:
                values[i] = 0


    def process_stats:
        # TODO:  Aggregate up the fleet's performance stats and...do what?  Print them?  Write them to a file?
