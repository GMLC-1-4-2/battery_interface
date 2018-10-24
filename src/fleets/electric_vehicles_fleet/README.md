# User Manual - Fleet of Electric Cars  

## GMLC 1.4.2/battery_interface
### Argonne National Laboratory - Advanced Mobility and Grid Integration Technology Research 

---

### Contributors
  - **Michael Duoba**: mduoba@anl.gov
  - **Alejandro Fernandez Canosa**: afernandezcanosa@anl.gov

### Description
 
This document provides the guidelines to use the `ElectricVehiclesFleet` class and describes its structure and basic functionality. Before starting with the description of the fleet, the assumptions of the model and the singularities of this fleet must be remarked:
  - Variability in the daily schedules of electric vehicles drivers. This variability makes the availability of the fleet limited to the moments when the cars are plugged-in.
  - User of electric cars want to have the control of their own charging strategy: electric cars manufacturers allow the users to choose among various charging strategies: start charging immediately, at midnight, or at a time to be fully charged before the beginning of the next day.
  - Bidirectional charging is not considered in this model. 

### Structure of the `ElectricVehiclesFleet` class:

#### 1. Instantiation of the class: `__init__(self, GridInfo, ts)`

##### 1.1. Important variables
Test
1. `self.run_baseline [type = bool, default = False]`: If `True`, Montecarlo simulations to store baseline power and SOC and, therefore, instantiate the SOC of the sub fleets and provide baseline power for the service power. If no changes are made in the configuration and parameters of the fleet, this variables should be kept equal to `False` as the baseline power and SOC is maintained.
2. `self.n_days_base [type = int, default = 10]`: Number of days with different driving schedules to average baseline power and SOC of the sub fleets.
3. `self.N_SubFleets [type = int, default = 100]`: Number of sub fleets. Each sub fleet has homogeneous properties. That is: same vehicle model, same number of vehicles, same driving schedule, etc. The larger the number of sub fleets, the better the results, but CPU time increases as the `N_SubFleets` does so.
4. `self.df_VehicleModels [type = pd.Dataframe]`: physical properties of the vehicle models that compose the fleet. **This dataframe reads the variables from the `vehicle_models.csv`** file. Therefore, if physical parameters have to be changed, modify the variables in the `.csv` file directly.
5. `self.ChargedAtWork_per [type = float, default = 0.17]`: percentage/100 of vehicles that are charged while working.
6. `self.ChargedAtOther_per [type = float, default = 0.02]`: percentage/100 of vehicles that are charged at other places (e.g. grocery store, high school).
7. `self.dt [type = int, default = 1]`: time step in seconds for `forecast` and `process_request` methods.
8. `self.strategies [type = list]`: percentage of sub fleets charging with the different charging strategies. For example:
	`self.strategies = [ ['right away', 'midnight', 'tcin'], [0.4, 0.3, 0.3] ]` means that 40 % of sub fleets are charged with the first charging strategy, 30 % with the second, and 30 % with the third one.

##### 1.2. Other variables
There are several variables in the constructor that have not been described in the previous section. These variables are either derived from the important variables and other data or parameters that must not be changed without the required expertise.

#### 2. Methods

Apart from the inherited methods of the `Fleet Interface` class, there are other methods that are described here:

1. `self.simulate(self, P_req, Q_req, initSOC, t, dt)`: this method is where all the main calculations are carried out. It takes the requested active and reactive power (`P_req` and `Q_req`, respectively), the SOC at time `t_0`, the local time of the class, `t` and the time step, `dt` and returns a `response` instance with the variables inherited from the `FleetResponse` class.



