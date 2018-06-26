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


class PeakManagementService():
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """

    def __init__(self, *args, **kwargs):
        self.sim_time_step = timedelta(hours=1)

        self.fleet = BatteryInverterFleet()

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

    def change_config(self):
        fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=0.1)
        self.fleet.change_config(fleet_config)

    def normalize_p(self, p):
        return p
