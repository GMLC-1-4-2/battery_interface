import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_config import FleetConfig
from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from services.peak_managment_service.peak_management_service import PeakManagementService


if __name__ == '__main__':

    # Instantiate a fleet for this test
    fleet = BatteryInverterFleet("ERM")

    # Set up the fleet (if necessary?)
    fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=None)

    # Instantiate a peak management service, connected to the previous fleet
    pms = PeakManagementService(fleet=fleet)

    # Do it
    pms.run_fleet_forecast_test()
