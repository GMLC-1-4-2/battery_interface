# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from dateutil import parser
from datetime import datetime, timedelta

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

    def __init__(self, fleet=None, capacity_scaling_factor=1.0, drive_cycle_file="drive.cycle.summer.peaky.csv", *args, **kwargs):

        self.drive_cycle_file = drive_cycle_file

        # Establish a default simulation timestep (in case drive cycle data has no time info?)...
        self.sim_time_step = timedelta(hours=1)

        # Set the appropriate fleet to use.
        # Q:  What's the best way to pass in the fleet to instantiate?  Should the fleet be
        # instantiated in main and passed in as an object?
        if fleet == None:
            self.fleet = BatteryInverterFleet()
        elif fleet = "HomeAcFleet":
            self.fleet = HomeAcFleet()
        else:
            self.fleet = None   # Need to throw an exception here...

        # Set up the fleet (if necessary?)
        fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=None)
        self.fleet.change_config(fleet_config)

        # Long term, we don't want a drive cycle, we want to call some kind of daily
        # load forecast service that a higher-level function in the software provides.
        # But for now, our whole purpose is testing...
        #
        # This data frame has columns (year, month, day, hour, load_forecast_mw)
        self.drive_cycle = pd.read_csv(self.drive_cycle_file)
        self.drive_cycle.load_forecast_mw /= self.capacity_scaling_factor

        # Ideally the fleet could tell us its capacity and we compute the scaling_factor from that
        # and the maximum value in the drive cycle...
        self.capacity_scaling_factor = capacity_scaling_factor


    def request(self):
        _ts = parser.parse("2017-08-01 16:00:00")
        _sim_step = timedelta(seconds=2)
        _p = self.normalize_p(100)
        fleet_request = FleetRequest(ts=_ts, sim_step=_sim_step, p=_p, q=None)

        fleet_response = self.fleet.process_request(fleet_request)

        return fleet_response

    def forecast(self):
        # Init simulation time frame
        start_time = datetime.utcnow()
        end_time = datetime.utcnow() + timedelta(hours=3)

        # Create requests for each hour in simulation time frame
        cur_time = start_time
        fleet_requests = []
        while cur_time < end_time:
            req = FleetRequest(ts=cur_time, sim_step=self.sim_time_step, p=1000, q=1000)
            fleet_requests.append(req)
            cur_time += self.sim_time_step

        # Call a fleet forecast
        forecast = self.fleet.forecast(fleet_requests)

        return forecast

    def run_fleet_test(self):
        foreach day
