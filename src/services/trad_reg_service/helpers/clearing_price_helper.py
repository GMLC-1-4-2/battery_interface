import pandas as pd
from dateutil import parser

class ClearingPriceHelper(object):

    def read_and_store_clearing_prices(self, input_data_file_path, start_time):
        """
        This method reads a given Excel file.
        Thus, this method is meant to be called only once reading Excel file takes
        a long time and we don't want to do it for getting every single value.
        """

        sheet_name = self._get_sheet_name(start_time)

        excel_data = pd.read_excel(input_data_file_path, sheet_name = sheet_name)
        # Get only the data whose 'SERVICE' is 'REG':
        regulated_prices_data_frame = excel_data[excel_data['SERVICE'] == 'REG']
        # Get only the columns we need:
        regulated_prices_data_frame = regulated_prices_data_frame[['LOCALDAY', 'LOCALHOUR',
                                                                'MCP', 'REG_CCP', 'REG_PCP']]
        # Create a new column 'LOCAL_DAY_HOUR':
        regulated_prices_data_frame['LOCAL_DAY_HOUR'] = regulated_prices_data_frame[
            'LOCALDAY'] + " " + regulated_prices_data_frame['LOCALHOUR'].map(str) + ":00:00"
        # Convert the type of column 'LOCAL_DAY_HOUR' to datetime.
        # Inside apply, parser.parse() converts string to datetime:
        regulated_prices_data_frame['LOCAL_DAY_HOUR'] = regulated_prices_data_frame[
            'LOCAL_DAY_HOUR'].apply(lambda x: parser.parse(x))
        # Get only the columns we need (i.e. We don't need 'LOCALDAY' and 'LOCALHOUR'):
        regulated_prices_data_frame = regulated_prices_data_frame[['LOCAL_DAY_HOUR', 'MCP',
                                                                'REG_CCP', 'REG_PCP']]
        regulated_prices_data_frame = regulated_prices_data_frame.set_index('LOCAL_DAY_HOUR')
        # Generate Dictionary. Index becomes key of Dictionary and the rest is put in tuple:
        regulated_prices_dictionary = regulated_prices_data_frame.T.apply(tuple).to_dict()
        self._clearing_prices = regulated_prices_dictionary

    @property
    def clearing_prices(self):
        return self._clearing_prices

    def _get_sheet_name(self, local_day):
        timestamp = pd.Timestamp(local_day)
        return timestamp.strftime("%B_%Y")
