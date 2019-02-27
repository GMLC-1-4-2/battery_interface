from datetime import datetime
from grid_info import GridInfo


def create_fleet(name, grid_type=1, **kwargs):
    if grid_type == 2:
        from grid_info_artificial_inertia import GridInfo  #Use for artificial Inertia case
        grid = GridInfo('Grid_Info_data_artificial_inertia.csv')
    else:
        from grid_info import GridInfo
        grid = GridInfo('Grid_Info_DATA_2.csv')

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
        dt = 30 * 60  # time step (in seconds)
        ts = datetime(2018, 9, 20, 5, 0, 00, 000000)

        fleet_test = ElectricVehiclesFleet(grid, ts)
        fleet_test.is_autonomous = False
        fleet_test.is_P_priority = True
        if 'autonomous' in kwargs and kwargs['autonomous']:
           fleet_test.is_autonomous = True
        fleet_test.VV11_Enabled = False
        fleet_test.FW21_Enabled = True
        fleet_test.dt = dt

        return fleet_test

    elif name == 'PV':
        from fleets.PV.PV_Inverter_Fleet import PVInverterFleet
        fleet = PVInverterFleet(GridInfo=grid)
        if 'autonomous' in kwargs and kwargs['autonomous']:
           fleet.is_autonomous = True
        fleet.VV11_Enabled = False
        fleet.FW21_Enabled = True
        return fleet
    elif name == 'WaterHeater':
        from fleets.water_heater_fleet.WH_fleet_control import WaterHeaterFleet
        fleet = WaterHeaterFleet()
        if 'autonomous' in kwargs and kwargs['autonomous']:
           fleet.is_autonomous = True
        fleet.VV11_Enabled = False
        fleet.FW21_Enabled = True
        return fleet

    elif name == 'HVAC':
        return None
    elif name == 'Refridge':
        return None


    raise "There is no fleet with name: " + name
