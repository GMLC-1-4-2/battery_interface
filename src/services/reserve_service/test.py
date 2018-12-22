import sys
from dateutil import parser
from os.path import dirname, abspath
from datetime import datetime
import pandas as pd

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from services.reserve_service.reserve_service import ReserveService

from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from grid_info import GridInfo


if __name__ == '__main__':

    # Battery Inverter Fleet
    grid = GridInfo('Grid_Info_DATA_2.csv')
    battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid, model_type='ERM')
    battery_inverter_fleet.is_autonomous = False
    battery_inverter_fleet.VV11_Enabled = False
    battery_inverter_fleet.FW21_Enabled = False

    service = ReserveService()
    service.fleet = battery_inverter_fleet

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
            'Period_from_Last_Event_Hours'])
    for month in monthtimes.keys():
        print('Starting ' + str(month) + ' at ' + datetime.now().strftime('%H:%M:%S'))
        start_time=parser.parse(monthtimes[month][0])
        fleet_response = service.request_loop(start_time=start_time,
                                              end_time=parser.parse(monthtimes[month][1]),
                                              clearing_price_filename=start_time.strftime('%Y%m') + '.csv',
                                              four_scenario_testing=False)
        all_results = pd.concat([all_results, fleet_response])
    print('Writing result .csv')
    file_dir = dirname(abspath(__file__)) + '\\results\\'
    all_results.to_csv(file_dir + datetime.now().strftime('%Y%m%d') + '_annual_results.csv')
    print('Duration:')
    print(datetime.now() - startTime)
