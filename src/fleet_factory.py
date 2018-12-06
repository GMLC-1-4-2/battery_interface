def create_fleet(name):
    if name == 'BatteryInverter':
        from grid_info import GridInfo
        from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet

        grid = GridInfo('Grid_Info_DATA_2.csv')
        battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid, model_type='ERM')
        battery_inverter_fleet.is_autonomous = False
        battery_inverter_fleet.VV11_Enabled = False
        battery_inverter_fleet.FW21_Enabled = False

        return battery_inverter_fleet

    elif name == 'WaterHeater':
        return None

    elif name == 'PV':
        return None