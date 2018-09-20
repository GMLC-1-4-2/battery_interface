# Testing the ElectricVehiclesFleet class

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pandas as pd

from fleet_request import FleetRequest
from fleet_response import FleetResponse
from electric_vehicles_fleet import ElectricVehiclesFleet

###############################################################################
# Test 1: test request and forecast methods

# Time stamp to start the simulation
ts = datetime(2018, 9, 20, 23, 0, 00, 000000)

# Instantiation of an object of the ElectricVehiclesFleet class
fleet_test = ElectricVehiclesFleet(ts)

dt = 60*30                                 # time step (in seconds)
seconds_of_simulation = 3600*12            # (in seconds)
local_time = fleet_test.get_time_of_the_day(ts)
t = np.arange(local_time,local_time+seconds_of_simulation,dt) # array of time in seconds 

# Read baseline power from Montecarlo simulations
dirname = os.path.dirname(__file__)
df_baseline = pd.read_csv(os.path.join(dirname,'data/power_baseline_charging_modes.csv' ))

power_baseline = (fleet_test.strategies[1][0]*df_baseline['power_RightAway_kW'].iloc[local_time:local_time+seconds_of_simulation] + 
                 fleet_test.strategies[1][1]*df_baseline['power_Midnight_kW'].iloc[local_time:local_time+seconds_of_simulation]  +
                 fleet_test.strategies[1][2]*df_baseline['power_TCIN_kW'].iloc[local_time:local_time+seconds_of_simulation])

# Initialization of the time step 
fleet_test.dt = dt

# Power requested (kW): test
power_request = 80000*(np.sin(2*np.pi*(t/seconds_of_simulation)))
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

power_service = []
max_power_service = []
power_response = []
energy_stored = np.zeros([len(t),])
for i in range(len(t)):  
    power_service.append(FORECAST[i].P_service)
    max_power_service.append(FORECAST[i].P_service_max)
    power_response.append(FORECAST[i].P_togrid)
    energy_stored[i] = FORECAST[i].E
    
    
"""
Parameters of the plots
"""
fig_s  = (9,6)
font_s = 14
font_w = 'bold'
lw = 1.75
leg_prop={"size": font_s-1}
    
plt.figure(figsize = fig_s)
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second} | {seconds_of_simulation/3600} hours of simulation | dt = {dt/60} min',
          fontsize = font_s + 2, fontweight = font_w)
plt.step(t - t[0], max_power_service, color = 'b', linewidth = lw, label = 'Max Service')
plt.step(t - t[0], power_service, color = 'k', linewidth = lw, label = 'Service')
plt.step(t - t[0], power_request, color = 'r', linewidth = lw, label = 'Request')
plt.grid()
plt.legend(prop = leg_prop)
plt.xlim([0,max(t) - t[0]])
plt.xlabel('$\Delta t$ (sec)', fontsize = font_s, fontweight = font_w)
plt.ylabel('Service Power (kW)', fontsize = font_s, fontweight = font_w)


plt.figure(figsize = fig_s)
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second} | {seconds_of_simulation/3600} hours of simulation | dt = {dt/60} min',
          fontsize = font_s + 2, fontweight = font_w)
plt.plot(np.arange(0,seconds_of_simulation), power_baseline, color = 'b', linewidth = lw, label = 'Baseline')
plt.step(t - t[0], power_response, color = 'k', linewidth = lw, label = 'Response')
plt.step(t - t[0], power_baseline[t] + power_request, color = 'r', linewidth = lw, label = 'Baseline + Request')
plt.grid()
plt.legend(prop = leg_prop)
plt.xlim([0,max(t) - t[0]])
plt.xlabel('$\Delta t$ (sec)', fontsize = font_s, fontweight = font_w)
plt.ylabel('Power (kW)', fontsize = font_s, fontweight = font_w)


plt.figure(figsize = fig_s)
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second} | {seconds_of_simulation/3600} hours of simulation | dt = {dt/60} min',
          fontsize = font_s + 2, fontweight = font_w)
plt.plot(t - t[0], energy_stored*1e-6, color = 'b', linewidth = lw)
plt.grid()
plt.xlim([0,max(t) - t[0]])
plt.xlabel('$\Delta t$ (sec)', fontsize = font_s, fontweight = font_w)
plt.ylabel('Energy stored (GW.h)', fontsize = font_s, fontweight = font_w)

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


plt.figure(figsize = fig_s)
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second} | {seconds_of_simulation/3600} hours of simulation | dt = {dt/60} min',
          fontsize = font_s + 2, fontweight = font_w)
plt.plot(t - t[0], SOC_fleet_time*100, color = 'b', linewidth = lw, label = 'Fleet')
plt.plot(t - t[0], SOC_right_away*100, 'r--', linewidth = lw, label = 'Right-away')
plt.plot(t - t[0], SOC_midnight*100, 'k--', linewidth = lw, label = 'Midnight')
plt.plot(t - t[0], SOC_tcin*100, 'c--', linewidth = lw, label = 'TCIN')
plt.grid()
plt.legend(prop = leg_prop)
plt.xlim([0,max(t) - t[0]])
plt.xlabel('$\Delta t$ (sec)', fontsize = font_s, fontweight = font_w)
plt.ylabel('SOC (%)', fontsize = font_s, fontweight = font_w)