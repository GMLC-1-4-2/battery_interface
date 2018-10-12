# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from dateutil import parser
from datetime import datetime, timedelta
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from fleet_config import FleetConfig


class ArtificialInertiaService():
    def __init__(self, fleet_device):
        self.fleet_device = fleet_device

    def request_loop(self):
        responses = []

        inittime = parser.parse("2018-10-12 00:00:00")
        delt = timedelta(seconds=2 / 60)
        cur_time = inittime
        end_time = cur_time + timedelta(seconds=60)
        while cur_time < end_time:
            fleet_request = FleetRequest(cur_time, delt)
            fleet_response = fleet_device.process_request(fleet_request)
            responses.append(fleet_response)
            cur_time += delt

        return responses

    def calculation(self, responses):
        # Do calculation with responses
        # responses []
        sum = 0
        for response in responses:
            p_togrid = response.P_togrid  # or P_service
            sum += p_togrid
        avg = sum / len(responses)

        return avg


if __name__ == "__main__":
    #import numpy as np
    #import matplotlib.pyplot as plt
    from grid_info import GridInfo
    from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
    from fleets.home_ac_fleet.home_ac_fleet import HomeAcFleet

    # Create a fleet and pass in gridinfo (contains the frequency from CSV file)
    grid = GridInfo('Grid_Info_DATA_2.csv')
    #fleet_device = BatteryInverterFleet(GridInfo=grid)  # establish the battery inverter fleet with a grid
    fleet_device = HomeAcFleet(GridInfo=grid)

    # Create a service
    service = ArtificialInertiaService(fleet_device)
    responses = service.request_loop()
    avg = service.calculation(responses)

    # Plot, print to screen ...
    print(avg)

