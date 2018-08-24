import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from services.trad_reg_service.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from services.trad_reg_service.trad_reg_service import TradRegService
from services.trad_reg_service.battery_inverter_fleet.grid_info import GridInfo


if __name__ == '__main__':
    service = TradRegService()

    # fleet = BatteryInverterFleet('C:\\Users\\jingjingliu\\gmlc-1-4-2\\battery_interface\\src\\fleets\\battery_inverter_fleet\\config_CRM.ini')
    grid = GridInfo('battery_inverter_fleet/Grid_Info_DATA_2.csv')
    fleet = BatteryInverterFleet(GridInfo=grid)  # establish the battery inverter fleet with a grid
    service.fleet = fleet

    # Test request_loop()
    fleet_response = service.request_loop()
    print(fleet_response)

