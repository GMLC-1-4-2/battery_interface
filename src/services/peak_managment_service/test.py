import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from services.peak_managment_service.peak_management_service import PeakManagementService


if __name__ == '__main__':

    # Instantiate a fleet for this test
    fleet = BatteryInverterFleet()

    # Set up the fleet (if necessary?)
    fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=None)

    # Instantiate a peak management service, connected to the previous fleet
    pms = PeakManagementService(
        fleet=None,
        capacity_scaling_factor=1.0,
        drive_cycle_file="drive.cycle.summer.peaky.csv",
        f_reduction=0.1)

    # Do it
    pms.run_fleet_forecast_test()
