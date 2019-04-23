import sys
from os.path import dirname, abspath
from src.fleets.electric_vehicles_fleet.electric_vehicles_fleet import ElectricVehiclesFleet
#from src.services.reg_service.test import fleet_name
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from dateutil import parser
from datetime import datetime, timedelta
from fleet_config import FleetConfig
from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from services.peak_managment_service.peak_management_service import PeakManagementService
from grid_info import GridInfo


if __name__ == '__main__':
    
    # Time stamp to start the simulation
    #ts = datetime(2018, 9, 20, 5, 0, 00, 000000)

    # Parameters of the grid
    grid = GridInfo('Grid_Info_DATA_2.csv')
    
    fleet_sim_step = timedelta(minutes=60)            
    # Instantiate a peak management service
    pms = PeakManagementService(sim_step=fleet_sim_step)   
    # Get start time for the simulation from drive cycle file
    start_time = pms.drive_cycle["dt"][0]
 
    # Instantiate a fleet for this test
    fleet = ElectricVehiclesFleet(grid, start_time)
    fleet.is_autonomous = False
    fleet.is_P_priority = True
    
    pms.fleet = fleet
    # Set up the fleet (if necessary?)
#    fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=None)
    fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, FW_Param=[], v_thresholds=[])

    # Instantiate a peak management service, connected to the previous fleet
    #pms = PeakManagementService(fleet=fleet)

    # Do it
    pms.request_loop(start_time,fleet_name='ElectricVehicle')
