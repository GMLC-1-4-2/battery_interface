import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from dateutil import parser

from services.trad_reg_service.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from services.trad_reg_service.trad_reg_service import TradRegService
from services.trad_reg_service.battery_inverter_fleet.grid_info import GridInfo


if __name__ == '__main__':
    service = TradRegService()

    # fleet = BatteryInverterFleet('C:\\Users\\jingjingliu\\gmlc-1-4-2\\battery_interface\\src\\fleets\\battery_inverter_fleet\\config_CRM.ini')
    grid = GridInfo('battery_inverter_fleet/Grid_Info_DATA_2.csv')
    battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid)  # establish the battery inverter fleet with a grid
    service.fleet = battery_inverter_fleet

    # Test request_loop()
    # Use line below for testing TRADITIONAL regulation service.
    # fleet_response = service.request_loop(service_type = "Traditional",
    #                                       start_time = parser.parse("2017-08-01 16:00:00"), end_time = parser.parse("2017-08-01 21:00:00"),
    #                                       clearing_price_filename = 'historical-ancillary-service-data-2017.xls')
    # Use line below for testing DYNAMIC regulation service.
    fleet_response = service.request_loop(service_type = "Dynamic",
                                          start_time = parser.parse("2017-08-01 16:00:00"), end_time = parser.parse("2017-08-02 15:00:00"),
                                          clearing_price_filename = 'historical-ancillary-service-data-2017.xls')

    # Print results in the 2-level dictionary.
    for key_1, value_1 in fleet_response.items():
        print(key_1)
        for key_2, value_2 in value_1.items():
            print('\t\t\t\t\t\t', key_2, value_2)
