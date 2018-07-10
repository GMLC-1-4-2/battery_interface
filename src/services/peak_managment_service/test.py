import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from services.peak_managment_service.peak_management_service import PeakManagementService


if __name__ == '__main__':

    fleet = BatteryInverterFleet()
    pms = PeakManagementService(
        fleet=None,
        capacity_scaling_factor=1.0,
        drive_cycle_file="drive.cycle.summer.peaky.csv",
        f_reduction=0.1)

    pms.run_fleet_forecast_test()
