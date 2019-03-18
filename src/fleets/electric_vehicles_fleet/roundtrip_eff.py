from datetime import datetime, timedelta
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

import sys
from os.path import dirname, abspath
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from grid_info import GridInfo


from fleets.electric_vehicles_fleet.electric_vehicles_fleet import ElectricVehiclesFleet



def main(ts, grid):
    
    # Instantiation of an object of the ElectricVehiclesFleet class
    fleet_test = ElectricVehiclesFleet(grid, ts)

    dt = 3600*1 # time step (in seconds)
    sim_step = timedelta(seconds = dt)
    seconds_of_simulation = 24*3600 # (in seconds)
    local_time = fleet_test.get_time_of_the_day(ts)
    t = np.arange(local_time,local_time+seconds_of_simulation,dt) # array of time in seconds 
    
    # Power requested (kW): test
    fleet_test.is_autonomous = False
    fleet_test.is_P_priority = True

    # List of requests
    requests = []
    for i in range(len(t)):
        req = FleetRequest(ts+i*sim_step, sim_step, ts, None, 0.)
        requests.append(req)
        
    FORECAST = fleet_test.forecast(requests)
    
    eff_charging = np.zeros([len(t), ])
    eff_discharging = np.zeros([len(t), ])
    for i in range(len(t)):  
        eff_charging[i] = FORECAST[i].Eff_charge
        eff_discharging[i] = FORECAST[i].Eff_discharge        
    
    return eff_charging, eff_discharging
    

if __name__ == "__main__":
    
    dirname = os.path.dirname(__file__)
    # Time stamp to start the simulation
    ts = datetime(2018, 9, 20, 00, 0, 00, 000000)    
    grid = GridInfo('Grid_Info_DATA_2.csv')
    
    e_in, e_out = main(ts, grid)
    
    # Compute the roundtrip efficiency matrix
    rt = np.multiply.outer(e_in*0.01, e_out*0.01)*100
    np.fill_diagonal(rt, 0)
    # Save the roundtrip efficiency matrix
    np.savetxt(os.path.join(dirname,'data/roundtrip_efficiency_electric_vehicle.csv'), rt, delimiter=",")
    
    fig, ax = plt.subplots()
    ax = sns.heatmap(rt, annot=False,  linewidths=.5)
    ax.set_title('Roundtrip efficiency matrix for EVs')
    ax.set_xlabel(r'$t_i$ (hr)')
    ax.set_ylabel(r'$t_j$ (hr)')
