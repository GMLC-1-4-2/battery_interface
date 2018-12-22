import sys
from dateutil import parser
from os.path import dirname, abspath
import pandas as pd

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from datetime import datetime
from services.reg_service.reg_service import RegService

from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
from grid_info import GridInfo
from datetime import datetime

from pdb import set_trace as bp 


if __name__ == '__main__':

    # Battery Inverter Fleet
    grid = GridInfo('Grid_Info_DATA_2.csv')
    battery_inverter_fleet = BatteryInverterFleet(GridInfo=grid, model_type='ERM')
    battery_inverter_fleet.is_autonomous = False
    battery_inverter_fleet.VV11_Enabled = False
    battery_inverter_fleet.FW21_Enabled = False

    service = RegService()
    service.fleet = battery_inverter_fleet


    # Test request_loop()
    # Use line below for testing TRADITIONAL regulation service.
    # fleet_response = service.request_loop(service_type="Traditional",
    #                                       start_time=parser.parse("2017-08-01 16:00:00"),
    #                                       end_time=parser.parse("2017-08-01 21:00:00"),
    #                                       clearing_price_filename='historical-ancillary-service-data-2017.xls')

    # Generate monthly start and end times to loop through
    monthtimes = dict({
                    'January': ["2017-01-01 00:00:00", "2017-01-31 23:59:58"],
                    'February': ["2017-02-01 00:00:00", "2017-02-28 23:59:58"],
                    'March': ["2017-03-01 00:00:00", "2017-03-30 23:59:58"],
                    'April': ["2017-04-01 00:00:00", "2017-04-30 23:59:58"],
                    'May': ["2017-05-01 00:00:00", "2017-05-31 23:59:58"],
                    'June': ["2017-06-01 00:00:00", "2017-06-30 23:59:58"],
                    'July': ["2017-07-01 00:00:00", "2017-07-31 23:59:58"],
                    'August': ["2017-08-01 00:00:00", "2017-08-31 23:59:58"],
                    'September': ["2017-09-01 00:00:00", "2017-09-30 23:59:58"],
                    'October': ["2017-10-01 00:00:00", "2017-10-31 23:59:58"],
                    'November': ["2017-11-01 00:00:00", "2017-11-30 23:59:58"],
                    'December': ["2017-12-01 00:00:00", "2017-12-31 23:59:58"]
                    })

    startTime = datetime.now()
    for service_type in ['Traditional', 'Dynamic']:
        all_results = pd.DataFrame(columns=['performance_score', 'hourly_integrated_MW',
                                        'mileage_ratio', 'Regulation_Market_Clearing_Price(RMCP)',
                                        'Reg_Clearing_Price_Credit'])
        for month in monthtimes.keys():
            print('Starting ' + str(month) + ' ' + service_type + ' at ' + datetime.now().strftime('%H:%M:%S'))
            fleet_response = service.request_loop(service_type=service_type,
                                                  start_time=parser.parse(monthtimes[month][0]),
                                                  end_time=parser.parse(monthtimes[month][1]),
                                                  clearing_price_filename='historical-ancillary-service-data-2017.xls')
            month_results = pd.DataFrame.from_dict(fleet_response, orient='index')
            all_results = pd.concat([all_results, month_results])
            print('     Finished ' + str(month) + ' ' + service_type)
        # Fix formatting of all_results dataframe to remove tuples
        all_results[['Perf_score', 'Delay_score', 'Corr_score', 'Prec_score']] = all_results['performance_score'].apply(pd.Series)
        all_results[['MCP', 'REG_CCP', 'REG_PCP']] = all_results['Regulation_Market_Clearing_Price(RMCP)'].apply(pd.Series)
        all_results[['Reg_Clr_Pr_Credit', 'Reg_RMCCP_Credit', 'Reg_RMPCP_Credit']] = all_results['Reg_Clearing_Price_Credit'].apply(pd.Series)
        all_results.drop(columns=['performance_score', 'Regulation_Market_Clearing_Price(RMCP)', 'Reg_Clearing_Price_Credit'],
                         inplace=True)
        print('Writing result .csv')
        file_dir = dirname(abspath(__file__)) + '\\results\\'
        all_results.to_csv(file_dir + datetime.now().strftime('%Y%m%d') + '_annual_hourlyresults_' + service_type + '_battery.csv')
    print('Duration:')
    print(datetime.now() - startTime)