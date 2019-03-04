from datetime import datetime
import numpy as np
import time
import os
import pandas as pd

import sys
from os.path import dirname, abspath
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from grid_info import GridInfo

from fleets.electric_vehicles_fleet.plot_test import Plots
from fleets.electric_vehicles_fleet.electric_vehicles_fleet import ElectricVehiclesFleet


###############################################################################
# Test 1: test request and forecast methods
dirname = os.path.dirname(__file__)

# Time stamp to start the simulation
ts = datetime(2018, 9, 20, 5, 0, 00, 000000)

# Parameters of the grid
grid = GridInfo('Grid_Info_DATA_2.csv')

# Instantiation of an object of the ElectricVehiclesFleet class
fleet_test = ElectricVehiclesFleet(grid, ts)
fleet_test.is_autonomous = False
fleet_test.is_P_priority = True

dt = 30*60                                  # time step (in seconds)
seconds_of_simulation = 24*3600             # (in seconds)
local_time = fleet_test.get_time_of_the_day(ts)
t = np.arange(local_time,local_time+seconds_of_simulation,dt) # array of time in seconds 

# Read baseline power from Montecarlo simulations
df_baseline = pd.read_csv(os.path.join(dirname,'data/power_baseline_charging_modes.csv' ))

power_baseline = - (fleet_test.strategies[1][0]*df_baseline['power_RightAway_kW'].iloc[local_time:local_time+seconds_of_simulation] + 
                    fleet_test.strategies[1][1]*df_baseline['power_Midnight_kW'].iloc[local_time:local_time+seconds_of_simulation]  +
                    fleet_test.strategies[1][2]*df_baseline['power_TCIN_kW'].iloc[local_time:local_time+seconds_of_simulation])

# Initialization of the time step 
fleet_test.dt = dt

# Power requested (kW): test
power_request = 50000*(1 + np.sin(2*np.pi*(t/seconds_of_simulation)))
#power_request = 50000*(np.ones([len(t),]))

# List of requests
requests = []
for i in range(len(t)):
    req = FleetRequest(ts, dt, power_request[i], 0.)
    requests.append(req)
   
print("SOC init = ", fleet_test.SOC)
# Measure cpu time
cpu_time = time.clock() 
FORECAST = fleet_test.forecast(requests)
cpu_time = (time.clock() - cpu_time)/len(t)
# check that the state of charge do not change when calling the forecast method
print("SOC check = ", fleet_test.SOC)
print("CPU time per time step = %f [sec]" %cpu_time)

power_service = []
max_power_service = []
power_response = []
energy_stored = np.zeros([len(t),])
for i in range(len(t)):  
    power_service.append(FORECAST[i].P_service)
    max_power_service.append(FORECAST[i].P_service_max)
    power_response.append(FORECAST[i].P_togrid)
    energy_stored[i] = FORECAST[i].E
 
#fleet_test.output_impact_metrics()  
#print("The impact metrics file has been produced: state of health of the batteries")
print(pd.read_csv('impact_metrics.csv'))

plots = Plots()
    
plots.service_power(t, power_service, power_request, ts, dt, seconds_of_simulation)
plots.power_to_grid(t, power_response, power_baseline, power_request, ts, dt, seconds_of_simulation)
plots.energy_fleet(t, energy_stored, ts, dt, seconds_of_simulation)

###############################################################################
# Test 2: test process_request method
# Initialization of important variables in the constructor
fleet_test.initial_time = fleet_test.get_time_of_the_day(ts)
fleet_test.time = fleet_test.get_time_of_the_day(ts)
fleet_test.dt = dt

# process the requests 
SOC_time = np.zeros([fleet_test.N_SubFleets, len(t)])
i = 0
for req in requests:
    fleet_test.process_request(req)
    # The SOC change!
    SOC_time[:,i] = fleet_test.SOC
    i+=1
    
SOC_fleet_time = np.mean(SOC_time, axis = 0)
SOC_right_away = np.mean(SOC_time[[i for i,x in enumerate(fleet_test.monitor_strategy) if x=='right away']], axis = 0)
SOC_midnight = np.mean(SOC_time[[i for i,x in enumerate(fleet_test.monitor_strategy) if x=='midnight']], axis = 0)
SOC_tcin = np.mean(SOC_time[[i for i,x in enumerate(fleet_test.monitor_strategy) if x=='tcin']], axis = 0)

plots.state_of_charge(t, SOC_fleet_time, SOC_right_away, SOC_midnight, SOC_tcin, ts, dt, seconds_of_simulation)