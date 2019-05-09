"""
Description: script to test the discretized autonomous response of the EV fleet.
This script can be used to tweak the range of the deadbands for this or other "discrete (ON/OFF)" devices

Last update: 03/18/2019
Author: afernandezcanosa@anl.gov
"""
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import sys
from os.path import dirname, abspath
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from grid_info_artificial_inertia import GridInfo
from fleets.electric_vehicles_fleet.electric_vehicles_fleet import ElectricVehiclesFleet

def main(ts, grid):
    
    # Instantiation of an object of the ElectricVehiclesFleet class
    fleet_test = ElectricVehiclesFleet(grid, ts)

    dt = 1                                   # time step (in seconds)
    sim_step = timedelta(seconds = dt)
    seconds_of_simulation = 149             # (in seconds)
    local_time = fleet_test.get_time_of_the_day(ts)
    t = np.arange(local_time,local_time+seconds_of_simulation,dt) # array of time in seconds 

    # Power requested (kW): test
    power_request = np.empty(len(t), dtype=object)
    fleet_test.is_autonomous = True
    fleet_test.is_P_priority = False

    # List of requests
    requests = []
    for i in range(len(t)):
        req = FleetRequest(ts+i*sim_step, sim_step, ts, power_request[i], 0.)
        requests.append(req)
    
    # power and frequency empty lists
    p = []
    f = []
    e_in = []
    i = 0
    SOC_time = np.zeros([fleet_test.N_SubFleets, len(t)])
    for req in requests:
        r = fleet_test.process_request(req)
        p.append(r.P_service)
        f.append(grid.get_frequency(req.ts_req, 0, req.start_time))
        e_in.append(r.Eff_charge)  
        print('t = %s' %str(req.ts_req))
        print('service power is = %f MW at f = %f Hz' %(p[i]/1e3, f[i]))

        SOC_time[:,i] = fleet_test.SOC
        i+=1
        
    p = np.array(p)
    f = np.array(f)  
    e_in = np.array(e_in)      
        
    return t-t[0], f, p/1000, e_in
        
if __name__ == "__main__":
    
    dirname = dirname(__file__)
    # Time stamp to start the simulation
    ts = datetime(2018, 9, 20, 17, 0, 00, 000000)
    
    # Parameters of the grid (ARTIFICIAL INERTIA)
    grid = GridInfo('Grid_Info_data_artificial_inertia.csv')
    
    time, freq, power, e_in = main(ts, grid)
    
    fig, ax1 = plt.subplots()
    ax1.set_title('Discretized Frequency Response for EVs - %s' %str(ts))
    ax1.plot(time, power, 'b-')
    ax1.set_ylabel('Service Power (MW)', color='b')
    ax1.tick_params('y', colors='b')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylim([-50, 350])

    ax2 = ax1.twinx()
    ax2.plot(time, 60-freq, 'r-')
    ax2.set_ylabel('60 - f (Hz)', color='r')
    ax2.tick_params('y', colors='r')

