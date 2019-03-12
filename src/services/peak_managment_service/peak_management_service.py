# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from dateutil import parser
from datetime import datetime, timedelta
import pandas as pd
import configparser

import utils
from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse
from fleet_config import FleetConfig


class PeakManagementService:
    """
    The peak management service short summary
    """

    def __init__(self, fleet, *args, **kwargs):
        # The scope of the project is to test service with one fleet...
        self.fleet = fleet

        # Get cur directory
        self.base_path = dirname(abspath(__file__))

        # Read config file
        config_header = 'config'
        self.config = configparser.ConfigParser()
        self.config.read(join(self.base_path, 'config.ini'))

        self.name = self.config.get(config_header, 'name', fallback='Peak Management Service')
        self.capacity_scaling_factor = float(self.config.get(config_header, 'capacity_scaling_factor', fallback=1.0))
        self.f_reduction = float(self.config.get(config_header, 'f_reduction', fallback=0.1))
        self.drive_cycle_file = self.config.get(config_header, 'drive_cycle_file',
                                                fallback='drive.cycle.summer.peaky.csv')
        self.drive_cycle_file = join(self.base_path, 'data', self.drive_cycle_file)

        # Establish a default simulation timestep (will always be 1-hour as far as I know)...
        self.sim_step = timedelta(hours=1)

        # Long term, we don't want a drive cycle, we want to call some kind of daily
        # load forecast service that a higher-level function in the software provides.
        # But for now, our whole purpose is testing...
        #
        # This data frame has columns (year, month_abbr, day, hour, load_forecast_mw), where month is
        # the three-letter month abbreviation (Jan, Feb, etc.) and all others are numeric...
        self.drive_cycle = pd.read_csv(self.drive_cycle_file)

        # There may be more straightforward ways to do this...just want to add a datetime object
        # matching the drive cycle's year, month_abbr, day, hour info...
        self.drive_cycle["month"] = [utils.month_abbr_to_num(abbr) for abbr in self.drive_cycle["month"]]

        # self.drive_cycle["dt"] = [datetime(self.drive_cycle["year"],
        #                                    self.drive_cycle["month_num"],
        #                                    self.drive_cycle["day"],
        #                                    self.drive_cycle["hour"], 0, 0)]

        self.drive_cycle["dt"] = pd.to_datetime(self.drive_cycle[["year", "month", "day", "hour"]])

        # Ideally the fleet could tell us its capacity and we compute the scaling_factor from that
        # and the maximum value in the drive cycle...
        self.drive_cycle.load_forecast_mw /= self.capacity_scaling_factor

        # Find the "annual" peak (largest peak in our drive cycle really) and the desired new peak...
        self.annual_peak = max(self.drive_cycle.load_forecast_mw)
        self.mw_target = self.annual_peak * (1 - self.f_reduction)

        # TODO:  Initialize something to hold stats

    def run_fleet_forecast_test(self):
        cycle = 24
        ndx_start = 0
        ndx_end = ndx_start + cycle
        while ndx_end < len(self.drive_cycle.dt):   # Loop over days...
            dt_day = self.drive_cycle.dt[ndx_start:ndx_end]
            dt_day.reset_index(drop=True, inplace=True)
            mw_day = self.drive_cycle.load_forecast_mw[ndx_start:ndx_end]
            mw_day.reset_index(drop=True, inplace=True)
            p_needed = [max(0, mw_day[i] - self.mw_target) for i in range(cycle)]

            ndx_start += 24
            ndx_end += 24

            # No need to work on days without high peaks
            if max(mw_day) <= self.mw_target:
                continue

            # Get a 24-hour forecast from fleet
            requests = [FleetRequest(ts=dt_day[i], sim_step=self.sim_step, p=p_needed[i]) for i in range(cycle)]
            forecast_response = self.fleet.forecast(requests)

            # See if the forecast can meet the desired load
            deficit = [forecast_response[i].P_service - p_needed[i] for i in range(24)]
            insufficient = [deficit[i] < 0 for i in range(cycle)]
            if any(insufficient):
                # TODO:  NEED TO LOOP BACK AND REBUILD requests until we have a 24-hour request we know can be met
                pass

            # Now we know what the fleet can do, so ask it to do it
            for i in range(24):
                fleet_request = FleetRequest(ts=dt_day[i], sim_step=self.sim_step, p=forecast_response[i].P_service)
                fleet_response = self.fleet.process_request(fleet_request)
                # TODO:  store performance stats

    def process_stats(self):
        pass
        # TODO:  Aggregate up the fleet's performance stats and...do what?  Print them?  Write them to a file?
