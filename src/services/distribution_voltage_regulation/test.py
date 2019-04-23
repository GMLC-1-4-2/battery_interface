# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from datetime import datetime
from dateutil import parser
import pandas as pd
import matplotlib.pyplot as plt
from os.path import dirname, abspath, join

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_factory import create_fleet
from service_factory import create_service


def integration_test(service_name, fleet_name, **kwargs):
    # Create test service
    service = create_service(service_name)
    if service is None:
        raise 'Could not create service with name ' + service_name


    grid_type = 2

    # Create test fleet
    fleet = create_fleet(fleet_name, grid_type, **kwargs)
    if fleet is None:
        raise 'Could not create fleet with name ' + fleet_name

    # Assign test fleet to test service to use
    service.fleet = fleet
    assigned_fleet_name = service.fleet.__class__.__name__

    start_time = kwargs['start_time']

    # Run test
    if service_name == 'DistributionVoltageService':
        fleet_responses, fleet_requests = service.request_loop()

    else:
        pass


if __name__ == '__main__':
    # Full test
    # services = ['Regulation', 'Reserve', 'ArtificialInertia' 'DistributionVoltageService']
    # fleets = ['BatteryInverter', 'ElectricVehicle', 'PV', 'WaterHeater', 'Electrolyzer', 'FuelCell', 'HVAC', 'Refridge' ]
    # kwargs = {'autonomous': True}  # This is for later use

    # Dev test
    services = ['DistributionVoltageService']
    fleets = ['PV']
    start_time = parser.parse('8/1/17 16:00')

    kwargs = {}
    kwargs['start_time'] = start_time

    for service in services:
        for fleet in fleets:
            if service == 'ArtificialInertia':
                kwargs['autonomous'] = 'autonomous'
            integration_test(service, fleet, **kwargs)
