# Test the ElectricVehiclesFleet class

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import time

from fleet_request import FleetRequest
from fleet_response import FleetResponse
from electric_vehicles_fleet import ElectricVehiclesFleet

# Test 1: test request and forecast methods

# Instantiation of an object of the ElectricVehiclesFleet class
fleet_test = ElectricVehiclesFleet()

# Time stamp to start the simulation
ts = datetime(2018, 7, 12, 7, 0, 00, 000000)
dt = 1                                     # time step (in seconds)
seconds_of_simulation = 5*60               # (in seconds)
t = np.arange(0,seconds_of_simulation,dt) 

# Initialization of important variables in the constructor
fleet_test.initial_time = fleet_test.get_time_of_the_day(ts)
fleet_test.time = fleet_test.get_time_of_the_day(ts)
fleet_test.dt = dt

# Power requested (kW): comment/uncomment
#power_request = 380000 + 400000*np.sin(0.1*t)*np.exp(-0.0001*t)
power_request = 250000*(t*np.exp(-40*t/(np.pi*seconds_of_simulation)))
#power_request  = 100000*np.ones([len(t),])

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

power_response = []
max_power_response = []
energy_stored = np.zeros([len(t),])
for i in range(len(t)):  
    power_response.append(FORECAST[i].P_injected)
    max_power_response.append(FORECAST[i].P_injected_max)
    energy_stored[i] = FORECAST[i].E
    
plt.figure(figsize = (12,8))
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second}', fontsize = 15, fontweight = 'bold')
plt.plot(t, max_power_response, color = 'b', label = 'max response')
plt.plot(t, power_response, color = 'k', label = 'response')
plt.plot(t, power_request, color = 'r', label = 'request')
plt.grid()
plt.legend()
plt.xlim([0,max(t)])
plt.xlabel('Time (sec)', fontsize = 14, fontweight = 'bold')
plt.ylabel('Power (kW)', fontsize = 14, fontweight = 'bold')

plt.figure(figsize = (12,8))
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second}', fontsize = 15, fontweight = 'bold')
plt.plot(t, energy_stored*1e-6, color = 'b')
plt.grid()
plt.xlim([0,max(t)])
plt.xlabel('Time (sec)', fontsize = 14, fontweight = 'bold')
plt.ylabel('Energy stored (GW.h)', fontsize = 14, fontweight = 'bold')

# Test 2: test process_request method

# process the requests 
SOC_time = np.zeros([fleet_test.N_SubFleets, len(t)])
i = 0
for req in requests:
    fleet_test.process_request(req.ts_req, req.P_req, req.Q_req)
    # The SOC change!
    SOC_time[:,i] = fleet_test.SOC
    i+=1
    
SOC_fleet_time = np.sum(SOC_time, axis = 0)/fleet_test.N_SubFleets

plt.figure(figsize = (12,8))
plt.title(f'Initial hour of request: {ts.hour}:{ts.minute}:{ts.second}', fontsize = 15, fontweight = 'bold')
plt.plot(t, SOC_fleet_time*100, color = 'b')
plt.grid()
plt.xlim([0,max(t)])
plt.xlabel('Time (sec)', fontsize = 14, fontweight = 'bold')
plt.ylabel('SOC (%)', fontsize = 14, fontweight = 'bold')