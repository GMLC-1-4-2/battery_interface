import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from battery_inverter_fleet import BatteryInverterFleet
from trad_reg_service import TradRegService


if __name__ == '__main__':
    service = TradRegService()

    # battery_inverter_fleet = BatteryInverterFleet('C:\\Users\\jingjingliu\\gmlc-1-4-2\\battery_interface\\src\\fleets\\battery_inverter_fleet\\config_CRM.ini')
    battery_inverter_fleet = BatteryInverterFleet()  # temporary for the purpose of getting dummy response
    service.fleet = battery_inverter_fleet

    # Test request_loop()
    fleet_response = service.request_loop()
    print(fleet_response)
