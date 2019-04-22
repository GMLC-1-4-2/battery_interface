# User Manual of the `HVACFleet`  

## GMLC 1.4.2 - battery_interface
### Oak Ridge National Laboratory

---

###  1. Contributors
  - **Teja Kuruganti**: kurugantipv@ornl.gov
  - **Jin Dong**: dongj@ornl.gov

### 2. Description
 
This document provides the guidelines to use the `HVACFleet` class and describes its structure and basic functionality. Assumptions of the model and singularities of this fleet are remarked here:
  - Variability in the daily schedules of electric vehicles drivers. This variability makes the availability of the fleet limited to the moments when the cars are plugged-in.
  - User of electric cars want to have the control of their own charging strategy: electric cars manufacturers allow the users to choose among various charging strategies: start charging immediately, at midnight, or at a time to be fully charged before the beginning of the next day.
  - Bidirectional charging is not considered in this model. 

### 3. Structure of the `HVACFleet` class:

### 3.1. Instantiation of the class: `__init__(self, GridInfo, ts)`

#### 3.1.1. Important variables

| Name                |  Type  |  Default | Description  |
|:-------------------:|:------:|:--------:|:-------------:|
| `self.run_baseline` |  `bool`|  `False` | If `True`, Run simulations to store baseline power and SOC are run. If `False`, the baseline power and SOC are maintained. |
| `self.numHVAC`    | `int`|   200    | Number of total HVAC units in the fleet. The larger the number of the fleet, the better the results, but CPU time increases as the `numHVAC` does so.   |
| `self.Tset`    | `real`|   23   | Average temperature setpoints across all the buildings in Celsius.  |
| `self.deadband`    | `real`|   0.5   | Traditional thermostat deadbands in Celsius.  |
| `self.dt`  | `int` | 1 | Time step in seconds for `forecast` and `process_request` methods. |


#### 3.1.2. Other variables

There are several variables in the constructor that have not been described in the previous section. These variables are either derived from the important variables and other data or parameters that must not be changed without the required expertise.

### 3.2. Methods

Apart from the inherited methods of the `FleetInterface` class, there are other methods that are described here:

1. `self.simulate(self, P_req, Q_req, initSOC, t, dt)`: This method is where all the main calculations are carried out. 
    * Prameters: 
      * `P_req`: active power requested.
      * `Q_req`: reactive power requested.
      * `initSOC`: initial SOC of the sub fleets.
      * `t`: local time of the class.
      * `dt`: time step
    * Returns:
      * `response`: an instance of the `FleetResponse` class.
      
2. `self.run_baseline_simulation(self)`: This method is used to simulate and restore baseline power and SOC. 
    * Parameters:
    * Returns:
      * It does not return anything, but it exports two csv files with the results of the SOC and the baseline power of the fleet.
    
### 4. Run tests

* Specify grid information and initial timestamp of request to instantiate the fleet:
```python 
from HVAC_fleet import HVACFleet
from datetime import datetime
ts = datetime(2018, 9, 20, 5, 0, 00, 000000)
grid = GridInfo(os.path.join(dirname, 'data/Grid_Info_DATA_2.csv'))
# Instantiation of the fleet
fleet_test = HVACFleet(grid, ts)
```

* Specify time step and simulation time:
```python
import numpy as np
dt = 30*60
fleet_test.dt = dt # in seconds
seconds_of_simulation = 3600*24
local_time = fleet_test.get_time_of_the_dat(ts)
t = np.arange(local_time, local_time + seconds_of_simulation, dt)
```

* Build request. For example, this dummy request:
```python
from fleet_request import FleetRequest
power_request = 50000*(1 + np.sin(2*np.pi(t/seconds_of_simulation))) #kW
# List of requests
requests = []
for i in range(len(t)):
  req = FleetRequest(ts, dt, power_request[i], 0.)
  requests.append(req)
```

* Run a forecast and export results (**This may take a while depending on the system**):

```python
FORECAST = fleet_test.forecast(requests)
# Store values as lists
power_service = []
max_power_service = []
power_response = []
energy_stored = np.zeros([len(t), ])
for i in range(len(t)):
  power_service.append(FORECAST[i].P_service)
  max_power_service.append(FORECAST[i].P_service_max)
  power_response.append(FORECAST[i].P_togrid)
  energy_stored[i] = FORECAST[i].E
```

* If desired, export impact metrics and print them by screen:
```python
import pandas as pd
fleet_test.output_metrics()
print(pd.read_csv('impact_metrics.csv'))
```

* Make the plots:
```python
from plot_test import Plots
plots = Plots()
plots.service_power(t, power_service, power_request, ts, dt, seconds_of_simulation)

# Read baseline power if want to visualize total power injected to the grid:
df_baseline = pd.read_csv(os.path.join(dirname,'data/power_baseline_charging_modes.csv' ))
power_baseline = (fleet_test.strategies[1][0]*df_baseline['power_RightAway_kW'].iloc[local_time:local_time+seconds_of_simulation] + 
                 fleet_test.strategies[1][1]*df_baseline['power_Midnight_kW'].iloc[local_time:local_time+seconds_of_simulation]  +
                 fleet_test.strategies[1][2]*df_baseline['power_TCIN_kW'].iloc[local_time:local_time+seconds_of_simulation])
plots.power_to_grid(t, power_response, power_baseline, power_request, ts, dt, seconds_of_simulation)
plots.energy_fleet(t, energy_stored, ts, dt, seconds_of_simulation)
```

* Test of the `process_request_method` is also shown. First, re-initialization of the fleet is required:
```python
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
```

### 4. Results and analysis

The response to a grid service request for one 24 hours-simulation is shown in this figure. As it can be observed, at the beginning of the day (5 AM), most of the vehicles are unplugged while driving, at work, or other places. Therefore, the fleet will not be able to track the grid service request. Once the sub fleets start arriving home after work around 4:30 PM, the fleet starts tracking the request accurately. Again, at the end of the day, when the TCIN constraint starts affecting, the request is not met.
