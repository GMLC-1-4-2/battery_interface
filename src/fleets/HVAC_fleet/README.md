# User Manual of the `HVACFleet`  

## GMLC 1.4.2 - battery_interface
### Oak Ridge National Laboratory

---

###  1. Contributors
  - **Teja Kuruganti**: kurugantipv@ornl.gov
  - **Jin Dong**: dongj@ornl.gov

### 2. Description
 
This document provides the guidelines to use the `HVACFleet` class and describes its structure and basic functionality. Assumptions of the model and singularities of this fleet are remarked here:
  - Variability in HVAC size, efficiency are randomly sampled from nominal building parameters.
  - Experior disturbance signals have been also randomly pciked from nominal weather file.
  - The model will auto interpolate the model and disturbance signals to run at any desired time resolutions.

### 3. Structure of the `HVACFleet` class:

### 3.1. Instantiation of the class: `__init__(self, GridInfo, ts)`

#### 3.1.1. Important variables

| Name                |  Type  |  Default | Description  |
|:-------------------:|:------:|:--------:|:-------------:|
| `self.run_baseline` |  `bool`|  `False` | If `True`, Run simulations to store baseline power and SOC are run. If `False`, the baseline power and SOC are maintained. |
| `self.numHVAC`    | `int`|   200    | Number of total HVAC units in the fleet. The larger the number of the fleet, the better the results, but CPU time increases as the `numHVAC` does so.   |
| `self.Tset`    | `real`|   23   | Average temperature setpoints across all the buildings in Celsius.  |
| `self.deadband`    | `real`|   2   | Traditional thermostat deadbands in Celsius.  |
| `self.dt`  | `int` | 10*60 | Default time step in seconds for `forecast` and `process_request` methods. |


#### 3.1.2. Other variables

There are several variables in the constructor that have not been described in the previous section. These variables are either derived from the important variables and other data or parameters that must not be changed without the required expertise.

### 3.2. Methods

Apart from the inherited methods of the `FleetInterface` class, there are other methods that are described here:

1. `self.simulate(self, P_req, Q_req, initSOC, t, dt)`: This method is where all the main calculations are carried out. 
    * Prameters: 
      * `P_req`: active power requested.
      * `Q_req`: reactive power requested.
      * `initSOC`: initial SOC of the fleet.
      * `t`: local time of the class.
      * `dt`: time step
    * Returns:
      * `response`: an instance of the `FleetResponse` class.
      
2. `self.run_baseline_simulation(self)`: This method is used to simulate and store baseline power, indoor temperatures, and SOC. 
    * Parameters:
    * Returns:
      * It does not return anything, but it exports several csv files with the results of the baseline power, indoor temperatures, and SOC of the fleet.
    
### 4. Run tests

A standard test is provided by running the 'test_jin.py' inside the '/src' folder.

* Specify grid information and initial timestamp of request to instantiate the fleet:
```python 
from HVAC_fleet import HVACFleet
from datetime import datetime
ts = datetime(2018, 9, 20, 5, 0, 00, 000000)
grid = GridInfo(os.path.join(dirname, 'data/Grid_Info_DATA_2.csv'))
# Instantiation of the fleet
fleet_test = HVACFleet(grid, ts, sim_step)
```

* Specify time step and simulation time:
```python
import numpy as np
dt = 10*60
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
