import pandas as pd
import numpy as np
from dateutil import parser

from pdb import set_trace as bp

class ClearingPriceHelper(object):

    # This method returns a Dictionary containing a month-worth of hourly SRMCP price data indexed by datetime.
    def read_and_store_clearing_prices(self, input_data_file_path, start_time):

        # This will only be necessary if we end up using an Excel spreadsheet with multiple tabs
        sheet_name = self._get_sheet_name(start_time)

        excel_data = pd.read_csv(input_data_file_path, skiprows=2)
        # Get only the data whose 'Subzone' is 'PJM Mid Atlantic Dominion (MAD)':
        reserve_prices_data_frame = excel_data[excel_data['Subzone'] == 'PJM Mid Atlantic Dominion (MAD)']
        # Get only the columns we need and rename the price column:
        reserve_prices_data_frame = reserve_prices_data_frame[['EPT Hour Ending', 'SRMCP ($/MWh)']]
        reserve_prices_data_frame.rename(columns={'SRMCP ($/MWh)': 'Price_SRMCP'}, inplace=True)
        # Split the 'EPT Hour Ending' time into date and hour ending columns
        reserve_prices_data_frame['Date'], reserve_prices_data_frame['Hour_End'] = reserve_prices_data_frame['EPT Hour Ending'].str.split(' ', 1).str

        # Calculate the start of the hour
        reserve_prices_data_frame['Hour_Start_Int'] = reserve_prices_data_frame['Hour_End'].map(int) - 1
        reserve_prices_data_frame['Hour_Start'] = np.where(reserve_prices_data_frame['Hour_Start_Int'] < 10,
            '0' + reserve_prices_data_frame['Hour_Start_Int'].astype(str),
            reserve_prices_data_frame['Hour_Start_Int'].astype(str))
        # Create a new column 'LOCAL_DAY_HOUR':
        reserve_prices_data_frame['LOCAL_DAY_HOUR'] = reserve_prices_data_frame[
            'Date'] + " " + reserve_prices_data_frame['Hour_Start'].map(str) + ":00:00"
        # Convert the type of column 'LOCAL_DAY_HOUR' to datetime and move time to start of hour.
        # Inside apply, parser.parse() converts string to datetime:
        reserve_prices_data_frame['LOCAL_DAY_HOUR'] = reserve_prices_data_frame[
            'LOCAL_DAY_HOUR'].apply(lambda x: parser.parse(x))
        # Get only the columns we need (i.e. We don't need 'LOCALDAY' and 'LOCALHOUR'):
        reserve_prices_data_frame = reserve_prices_data_frame[['LOCAL_DAY_HOUR', 'Price_SRMCP']]
        reserve_prices_data_frame = reserve_prices_data_frame.set_index('LOCAL_DAY_HOUR')
        # Generate Dictionary. Index becomes key of Dictionary and the rest is put in tuple:
        reserve_prices_data_frame = reserve_prices_data_frame.T.apply(tuple).to_dict()
        self._clearing_prices = reserve_prices_data_frame

    # Use "dependency injection" to allow method "clearing_prices" be used as an attribute.
    @property
    def clearing_prices(self):
        return self._clearing_prices

    # Get name of the tab in the Excel file holding price data for a whole year.
    def _get_sheet_name(self, local_day):
        timestamp = pd.Timestamp(local_day)
        return timestamp.strftime("%Y%m")
