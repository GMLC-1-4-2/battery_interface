# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 16:45:44 2019

@author: huang38
"""

import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

#from fleet_config import FleetConfig
#from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
#from services.peak_managment_service.peak_management_service import PeakManagementService
from services.energy_market_service.energy_market_service import dispatch_algorithm as da

#if __name__ == '__main__':

#    # Instantiate a fleet for this test
#    fleet = BatteryInverterFleet("ERM")
#
#    # Set up the fleet (if necessary?)
#    fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=None)
#
#    # Instantiate a peak management service, connected to the previous fleet
#    pms = PeakManagementService(fleet=fleet)
#
#    # Do it
#    pms.run_fleet_forecast_test()
    
#obj = EnergyMarketService()
maxValue = da() 
