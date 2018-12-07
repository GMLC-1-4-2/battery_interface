import sys
from dateutil import parser
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from services.reserve_service.reserve_service import ReserveService

from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from grid_info import GridInfo


if __name__ == '__main__':

    # Battery Inverter Fleet
    grid = GridInfo('Grid_Info_DATA_2.csv')
    battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid, model_type='ERM')
    battery_inverter_fleet.is_autonomous = False
    battery_inverter_fleet.VV11_Enabled = False
    battery_inverter_fleet.FW21_Enabled = False

    service = ReserveService()
    service.fleet = battery_inverter_fleet


    # Test request_loop()
    # Use line below for testing TRADITIONAL regulation service.
    # fleet_response = service.request_loop(service_type="Traditional",
    #                                       start_time=parser.parse("2017-08-01 16:00:00"),
    #                                       end_time=parser.parse("2017-08-01 21:00:00"),
    #                                       clearing_price_filename='historical-ancillary-service-data-2017.xls')

    # Use line below for testing DYNAMIC regulation service.
    fleet_response = service.request_loop(start_time=parser.parse("2017-01-01 00:00:00"),
                                          end_time=parser.parse("2017-01-01 05:00:00"),
                                          clearing_price_filename="201701.csv")

    # Print results in the 2-level dictionary.
    '''for key_1, value_1 in fleet_response.items():
                    print(key_1)
                    for key_2, value_2 in value_1.items():
                        print('\t\t\t\t\t\t', key_2, value_2)'''
