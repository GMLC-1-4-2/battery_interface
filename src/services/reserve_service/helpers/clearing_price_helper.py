import pandas as pd
import numpy as np
from dateutil import parser

from pdb import set_trace as bp

class ClearingPriceHelper(object):

    # This method returns a Dictionary containing a month-worth of hourly SRMCP price data indexed by datetime.
    def read_and_store_clearing_prices(self, input_data_file_path, start_time):
        # Read file.
        excel_data = pd.read_csv(input_data_file_path, skiprows=2)
        # Get only the data whose 'Subzone' column is 'PJM Mid Atlantic Dominion (MAD)':
        reserve_prices_data_frame = excel_data[excel_data['Subzone'] == 'PJM Mid Atlantic Dominion (MAD)']
        # Get only the columns we need and rename the price column:
        reserve_prices_data_frame = reserve_prices_data_frame[['EPT Hour Ending', 'SRMCP ($/MWh)']]
        # Split the 'EPT Hour Ending' time into date and hour ending columns
        reserve_prices_data_frame['Date'], reserve_prices_data_frame['Hour_End'] = reserve_prices_data_frame['EPT Hour Ending'].str.split(' ', 1).str

        # Calculate the start of the hour from the ending of the hour.
        reserve_prices_data_frame['Hour_Start_Int'] = reserve_prices_data_frame['Hour_End'].map(int) - 1
        # TODO: what does "<10" do?
        reserve_prices_data_frame['Hour_Start'] = np.where(reserve_prices_data_frame['Hour_Start_Int'] < 10,
            '0' + reserve_prices_data_frame['Hour_Start_Int'].astype(str),
            reserve_prices_data_frame['Hour_Start_Int'].astype(str))
        # Create a new column 'LOCAL_DAY_HOUR':
        reserve_prices_data_frame['LOCAL_DAY_HOUR'] = reserve_prices_data_frame[
            'Date'] + " " + reserve_prices_data_frame['Hour_Start'].map(str) + ":00:00"
        # Convert the type of column 'LOCAL_DAY_HOUR' to datetime and move time to start of the hour.
        # Inside apply, parser.parse() converts string to datetime:
        reserve_prices_data_frame['LOCAL_DAY_HOUR'] = reserve_prices_data_frame[
            'LOCAL_DAY_HOUR'].apply(lambda x: parser.parse(x))
        # Get only the columns we need (get rid of columns generated during intermediate steps):
        reserve_prices_data_frame = reserve_prices_data_frame[['LOCAL_DAY_HOUR', 'SRMCP ($/MWh)']]
        reserve_prices_data_frame = reserve_prices_data_frame.set_index('LOCAL_DAY_HOUR')
        # Generate Dictionary. Index becomes key of Dictionary and the rest is put in tuple:
        # TODO: can you explain a little more why we need tuple here? I thought there's only one column left "SRMCP" other than the index column.
        reserve_prices_data_frame = reserve_prices_data_frame.T.apply(tuple).to_dict()
        self._clearing_prices = reserve_prices_data_frame

    # Allow method "clearing_prices" be used as an attribute.
    @property
    def clearing_prices(self):
        return self._clearing_prices

