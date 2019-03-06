from datetime import datetime
from grid_info import GridInfo

grid1 = GridInfo('Grid_Info_DATA_2.csv')
#grid2 = GridInfo('Grid_Info_data_artificial_inertia.csv')


def create_fleet(name, grid_type=1, **kwargs):
    #grid = grid1 if grid_type == 1 else grid2
    grid = grid1

    if name == 'BatteryInverter':
        from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
        battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid, model_type='ERM')
        battery_inverter_fleet.is_autonomous = False
        if 'autonomous' in kwargs and kwargs['autonomous']:
            battery_inverter_fleet.is_autonomous = True
        battery_inverter_fleet.VV11_Enabled = False
        battery_inverter_fleet.FW21_Enabled = False

        return battery_inverter_fleet

    elif name == 'ElectricVehicle':
        from fleets.electric_vehicles_fleet.electric_vehicles_fleet import ElectricVehiclesFleet

        # Time stamp to start the simulation
        # Please, ensure that the timestamp is the same timestamp passed at the
        # beginning of the service request
        ts = datetime(2018, 9, 20, 16, 0, 00, 000000)

        fleet_test = ElectricVehiclesFleet(grid, ts)
        fleet_test.is_autonomous = False
        fleet_test.is_P_priority = True

        return fleet_test

    elif name == 'PV':
        from fleets.PV.PV_Inverter_Fleet import PVInverterFleet
        fleet = PVInverterFleet(GridInfo=grid)

        return fleet
    elif name == 'WaterHeater':
        from fleets.water_heater_fleet.WH_fleet_control import WaterHeaterFleet
        fleet = WaterHeaterFleet()
        return fleet

    elif name == 'HVAC':
        return None
    elif name == 'Refridge':
        return None


    raise "There is no fleet with name: " + name
