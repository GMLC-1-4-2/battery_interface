# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from dateutil import parser
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_factory import create_fleet
from service_factory import create_service


def integration_test(service_name, fleet_name, **kwargs):
    # Create test service
    service = create_service(service_name)
    if service is None:
        raise 'Could not create service with name ' + service_name

    grid_type = 1
    if service_name == 'ArtificialInertia':
        grid_type = 2

    # Create test fleet
    fleet = create_fleet(fleet_name, grid_type, **kwargs)
    if fleet is None:
        raise 'Could not create fleet with name ' + fleet_name

    # Assign test fleet to test service to use
    service.fleet = fleet

    # Run test
    if service_name == 'Regulation':
        fleet_responses = service.request_loop(service_type='Dynamic',
                                              start_time=parser.parse('2017-08-01 16:00:00'),
                                              # end_time=parser.parse('2017-08-02 15:00:00'),
                                              end_time=parser.parse('2017-08-01 23:00:00'),
                                              clearing_price_filename='historical-ancillary-service-data-2017.xls')
        for key_1, value_1 in fleet_responses.items():
            for key_2, value_2 in value_1.items():
                print('\t\t\t\t\t\t', key_2, value_2)

    elif service_name == 'ArtificialInertia':
        fleet_responses = service.request_loop()
        avg = service.calculation(fleet_responses)
        print(avg)

    else:
        pass



if __name__ == '__main__':
    # Full test
    # services = ['Regulation', 'ArtificialInertia']
    # fleets = ['BatteryInverter', 'ElectricVehicle', 'PV', 'WaterHeater', 'HVAC', 'Refridge' ]
    # kwargs = {'autonomous': True}  # This is for later use

    # Dev test
    services = ['Regulation']
    fleets = ['WaterHeater']
    kwargs = {}

    for service in services:
        for fleet in fleets:
            integration_test(service, fleet, **kwargs)
