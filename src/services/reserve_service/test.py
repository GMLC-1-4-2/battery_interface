import sys
from dateutil import parser
from os.path import dirname, abspath
from datetime import datetime
import pandas as pd

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from services.reserve_service.reserve_service import ReserveService

from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from fleets.electric_vehicles_fleet.electric_vehicles_fleet import ElectricVehiclesFleet
from grid_info import GridInfo


if __name__ == '__main__':

    # Battery Inverter Fleet
    grid = GridInfo('Grid_Info_DATA_2.csv')
    battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid, model_type='ERM')
    battery_inverter_fleet.is_autonomous = False
    battery_inverter_fleet.VV11_Enabled = False
    battery_inverter_fleet.FW21_Enabled = False

    # Test with EV.
    # Time stamp to start the simulation
    dt = 2  # time step (in seconds) Is this used anywhere in the EV model?
    ts = datetime(2017, 1, 1, 0, 0, 00, 000000)

    fleet_test = ElectricVehiclesFleet(grid, ts)
    fleet_test.is_autonomous = False
    fleet_test.is_P_priority = True
    fleet_test.dt = dt

    # Test with PV.
    from fleets.PV.PV_Inverter_Fleet import PVInverterFleet
    fleet = PVInverterFleet(GridInfo=grid)

    # Test
    service = ReserveService()
    service.fleet = battery_inverter_fleet

    # For a short test run, can use code below instead of running for the full year,
    # which takes ~12 minutes to run.
    # monthtimes = dict({
    #                 'January':   ["2017-01-01 00:00:00", "2017-01-31 23:59:59"],
    #                 'February':  ["2017-02-01 00:00:00", "2017-02-28 23:59:59"],
    #                 'March':     ["2017-03-01 00:00:00", "2017-03-31 23:59:59"],
    #                 'April':     ["2017-04-01 00:00:00", "2017-04-30 23:59:59"],
    #                 })

    # Generate monthly start and end times to loop through 
    monthtimes = dict({
                    'January':   ["2017-01-01 00:00:00", "2017-01-31 23:59:59"],
                    'February':  ["2017-02-01 00:00:00", "2017-02-28 23:59:59"],
                    'March':     ["2017-03-01 00:00:00", "2017-03-31 23:59:59"],
                    'April':     ["2017-04-01 00:00:00", "2017-04-30 23:59:59"],
                    'May':       ["2017-05-01 00:00:00", "2017-05-31 23:59:59"],
                    'June':      ["2017-06-01 00:00:00", "2017-06-30 23:59:59"],
                    'July':      ["2017-07-01 00:00:00", "2017-07-31 23:59:59"],
                    'August':    ["2017-08-01 00:00:00", "2017-08-31 23:59:59"],
                    'September': ["2017-09-01 00:00:00", "2017-09-30 23:59:59"],
                    'October':   ["2017-10-01 00:00:00", "2017-10-31 23:59:59"],
                    'November':  ["2017-11-01 00:00:00", "2017-11-30 23:59:59"],
                    'December':  ["2017-12-01 00:00:00", "2017-12-31 23:59:00"]
                    })

    # Get name of fleet for inclusion in results file names
    # and specify it as a load or not
    fleet_name = fleet.__class__.__name__

    startTime = datetime.now()
    all_results = pd.DataFrame(columns=['Event_Start_Time', 'Event_End_Time',
            'Response_to_Request_Ratio', 'Response_MeetReqOrMax_Index_number',
            'Event_Duration_mins', 'Response_After10minToEnd_To_First10min_Ratio',
            'Requested_MW', 'Responded_MW_at_10minOrEnd', 'Shortfall_MW',
            'Response_0min_Min_MW', 'Response_10minOrEnd_Max_MW',
            'Response_After10minToEnd_MW', 'SRMCP_DollarsperMWh_DuringEvent',
            'SRMCP_DollarsperMWh_SinceLastEvent',
            'Service_Value_NotInclShortfall_dollars',
            'Service_Value_InclShortfall_dollars',
            'Period_from_Last_Event_Hours',
            'Period_from_Last_Event_Days'])
    if 'battery' in fleet_name.lower():
        annual_signals = pd.DataFrame(columns=['Date_Time', 'Request', 'Response', 'SOC'])
    else:
        annual_signals = pd.DataFrame(columns=['Date_Time', 'Request', 'Response'])
    # Set previous event end to be 20170101, since nothing comes before the first event
    # (This is for calculating the shortfall of the first event, if applicable)
    previous_event_end = pd.Timestamp('01/01/2017 00:00:00')
    for month in monthtimes.keys():
        print('Starting ' + str(month) + ' at ' + datetime.now().strftime('%H:%M:%S'))
        start_time=parser.parse(monthtimes[month][0])
        fleet_response = service.request_loop(fleet_is_load=False,
                                              start_time=start_time,
                                              end_time=parser.parse(monthtimes[month][1]),
                                              clearing_price_filename=start_time.strftime('%Y%m') + '.csv',
                                              previous_event_end=previous_event_end,
                                              four_scenario_testing=False,
                                              fleet_name=fleet_name)
        try:
            previous_event_end = fleet_response.Event_End_Time[-1]
        except:
            pass
        
        all_results = pd.concat([all_results, fleet_response[0]])
        annual_signals = pd.concat([annual_signals, fleet_response[1]])
        
    print('Writing result .csv')
    file_dir = dirname(abspath(__file__)) + '\\results\\'
    all_results.to_csv(file_dir + datetime.now().strftime('%Y%m%d') + '_annual_results_reserve_' + fleet_name + '.csv')
    print('Plotting annual signals and SOC (if necessary)')
    plot_dir = dirname(abspath(__file__)) + '\\results\\plots\\'
    plot_filename = datetime.now().strftime('%Y%m%d') + '_annual_signals_' + fleet_name + '.png'
    plt.figure(1)
    plt.figure(figsize=(15,8))
    plt.subplot(211)
    plt.plot(annual_signals.Date_Time, annual_signals.Request, label='P Request')
    plt.plot(annual_signals.Date_Time, annual_signals.Response, label='P Response')
    plt.ylabel('Power (kW)')
    plt.legend(loc='best')
    if 'battery' in fleet_name.lower():
        plt.subplot(212)
        plt.plot(annual_signals.Date_Time, annual_signals.SoC, label='SoC')
        plt.ylabel('SoC (%)')
        plt.xlabel('Time')
    plt.savefig(plot_dir + plot_filename, bbox_inches='tight')
    plt.close()
    print('Duration:')
    print(datetime.now() - startTime)
