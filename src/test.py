# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys, os
from dateutil import parser
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_factory import create_fleet
from service_factory import create_service


def integration_test():
    # Create test fleet
    fleet = create_fleet('BatteryInverter')

    # Create test service
    service = create_service('Regulation')

    # Assign test fleet to test service to use
    service.fleet = fleet

    # Run test
    fleet_response = service.request_loop(service_type='Dynamic',
                                          start_time=parser.parse('2017-08-01 16:00:00'),
                                          end_time=parser.parse('2017-08-02 15:00:00'),
                                          clearing_price_filename='historical-ancillary-service-data-2017.xls')

    # Print results in the 2-level dictionary.
    for key_1, value_1 in fleet_response.items():
        print(key_1)
        for key_2, value_2 in value_1.items():
            print('\t\t\t\t\t\t', key_2, value_2)


if __name__ == '__main__':
    integration_test()
