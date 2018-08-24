import pandas as pd
from dateutil import parser

class ClearingPriceHelper(object):

    def read_and_store_clearing_prices(self, input_data_file_path, start_time):

        sheet_name = self._get_sheet_name(start_time)

        excel_data = pd.read_excel(input_data_file_path, sheet_name = sheet_name)
        regulated_prices_data_frame = excel_data[excel_data['SERVICE'] == "REG"]
        regulated_prices_data_frame = regulated_prices_data_frame[['LOCALDAY', "LOCALHOUR", 'MCP', 'REG_CCP', 'REG_PCP']]
        regulated_prices_data_frame['LOCAL_DAY_HOUR'] = regulated_prices_data_frame['LOCALDAY'] + " " + regulated_prices_data_frame['LOCALHOUR'].map(str) + ":00:00"
        regulated_prices_data_frame['LOCAL_DAY_HOUR'] = regulated_prices_data_frame['LOCAL_DAY_HOUR'].apply(lambda x: parser.parse(x))
        regulated_prices_data_frame = regulated_prices_data_frame[['LOCAL_DAY_HOUR', 'MCP', 'REG_CCP', 'REG_PCP']]
        regulated_prices_data_frame = regulated_prices_data_frame.set_index('LOCAL_DAY_HOUR')
        regulated_prices_dictionary = regulated_prices_data_frame.T.apply(tuple).to_dict()
        self._clearing_prices = regulated_prices_dictionary

    @property
    def clearing_prices(self):
        return self._clearing_prices

    def _get_sheet_name(self, local_day):
        timestamp = pd.Timestamp(local_day)
        return timestamp.strftime("%B_%Y")
