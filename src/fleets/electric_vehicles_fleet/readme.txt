README
"electric_vehicles_fleet.py" 
The following readme.txt describes the structure of the class ElectricVehiclesFleet(FleetInterface) contained in the python "electric_vehicles_fleet.py" file
Describes its functionality, methods, and attributes.
@authors: mduoba@anl.gov 
	  afernandezcanosa@anl.gov
Last update: 07/20/2018
Argonne National Laboratory (ANL) - Grid Modernization Lab Consortium (GMLC)
--------------------------------------------------------------------------------------------------------------------------------------------------------------

HOW TO RUN A SIMPLE "test.py":

First, instantiate the ElectricVehiclesFleet as usual in python (fleet_test = ElectricVehiclesFleet(ts)). 

It is important to mention that each sub fleet is connected or disconnected depending on the schedule, their charging strategy, etc.

After specifying a timestep, dt, a list of requests is made by using the "FleetRequest" class. For example, 

for i in range(len(t)):
    req = FleetRequest(ts, dt, power_request[i], 0.)
    requests.append(req)

Once the requests are appended into a list, the forecast method of the ElectricVehiclesFleet class can be called, and its values can be stored in a different 
variable.

FORECAST = fleet_test.forecast(requests)

power_response = []
max_power_response = []
for i in range(len(t)):  
    power_response.append(FORECAST[i].P_injected)
    max_power_response.append(FORECAST[i].P_injected_max)