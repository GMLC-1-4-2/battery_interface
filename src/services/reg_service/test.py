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
                    'March': ["2017-03-01 00:00:00", "2017-03-31 23:59:58"],
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
    all_results = pd.DataFrame(columns=['performance_score', 'hourly_integrated_MW',
                                        'mileage_ratio', 'Regulation_Market_Clearing_Price(RMCP)',
                                        'Reg_Clearing_Price_Credit'])
    startTime = datetime.now()
    for month in ['January']:
        print('Starting ' + str(month))
        fleet_response = service.request_loop(service_type="Dynamic",
                                              start_time=parser.parse(monthtimes[month][0]),
                                              end_time=parser.parse(monthtimes[month][1]),
                                              clearing_price_filename='historical-ancillary-service-data-2017.xls')
        month_results = pd.DataFrame.from_dict(fleet_response, orient='index')
        all_results = pd.concat([all_results, month_results])
        print('     Finished ' + str(month))
    print('Duration:')
    print(datetime.now() - startTime)
    bp()
    print('Writing .csv')
    all_results.write_csv(datetime.now().strftime('%Y%m%d') + '_annual_reg_service_results.csv')
    '''# Print results in the 2-level dictionary.
                for key_1, value_1 in fleet_response.items():
                    print(key_1)
                    for key_2, value_2 in value_1.items():
                        print('\t\t\t\t\t\t', key_2, value_2)'''
