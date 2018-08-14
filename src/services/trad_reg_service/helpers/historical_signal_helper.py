import pandas as pd
import datetime
from services.exceptions.datetime_validation_exception import DatetimeValidationException

class HistoricalSignalHelper(object):

    def read_and_store_historical_signals(self, input_data_file_path, sheet_name):

        excel_data = pd.read_excel(input_data_file_path, sheet_name = sheet_name, index = 0)
        # TODO: For now, drop the last row.
        #       Convert the index to multiple indices with hour, minute, and second.
        #       Or convert to Pandas.TimeDelta.
        # Note: It turned out that the first row value of the next column is same as the last row value of the given column.
        #       Thus, when stacking all the columns, the last row values must be removed.
        excel_data = excel_data.drop(excel_data.index[len(excel_data.index) - 1])

        self._signals = excel_data

    def signals_in_range(self, start_time, end_time):
        self._validate_date_range(start_time, end_time)

        if start_time.date() == end_time.date():
            return self._signals_in_range_within_the_same_day(start_time, end_time)
        else:
            return self._signals_in_range_encompassing_multiple_days(start_time, end_time)

    @property
    def signals(self):
        return self._signals

    def _signals_in_range_within_the_same_day(self, start_time, end_time):
        beginning_of_the_day = pd.Timestamp(f"{start_time.year}-{start_time.month}-{start_time.day}")
        series_for_day = self._signals[beginning_of_the_day]
        series_in_range = series_for_day[datetime.time(start_time.hour, start_time.minute, start_time.second):datetime.time(end_time.hour, end_time.minute, end_time.second)]
        series_in_range_with_datetime_index = self._convert_index_to_datetime(series_in_range, start_time)
        return series_in_range_with_datetime_index.to_dict()

    def _signals_in_range_encompassing_multiple_days(self, start_time, end_time):
        transposed_signals = self._signals.T
        stacked_signals = transposed_signals.stack().reset_index()
        stacked_signals.rename(columns = { stacked_signals.columns[0]: 'date', stacked_signals.columns[1]: 'time' }, inplace = True)
        stacked_signals['timestamp'] = stacked_signals.apply(lambda row: pd.datetime.combine(row['date'], row['time']), 1)
        stacked_signals.set_index('timestamp', inplace = True)
        stacked_signals.drop(['date', 'time'], axis = 1, inplace = True)
        signals_in_range = stacked_signals[start_time:end_time].squeeze() # Use squeeze() converts DataFrame to Series in order to get expected dictionary format.
        return signals_in_range.to_dict() # When to_dict is called, Series converts Timestamp to datatime while DataFrame doesn't.

    def _convert_index_to_datetime(self, series, start_time):
        index_list = series.index.tolist()
        datetime_index_list = [datetime.datetime.combine(start_time, index) for index in index_list]
        series.index = datetime_index_list
        return series

    def _validate_date_range(self, start_time, end_time):
        if start_time > end_time:
            raise DatetimeValidationException("Start time: {}, End time: {}. Start time must not be after end time.".format(start_time, end_time))

        if start_time.year != end_time.year or start_time.month != end_time.month:
            raise DatetimeValidationException("Start time: year = {} month = {}, End time: year = {} month = {}. Start date and end date must be in the same month. Currently, range in multiple months is not supported.".format(start_time.year, start_time.month, end_time.year, end_time.month))

        first_day_in_data = self._signals.columns[0]
        if start_time < first_day_in_data or end_time < first_day_in_data:
            raise DatetimeValidationException("Start time: year = {} month = {}, End time: year = {} month = {}. Input data: year = {} month = {}. Start time and end time must be within the date range of given data.".format(start_time.year, start_time.month, end_time.year, end_time.month, first_day_in_data.year, first_day_in_data.month))
        last_day_in_data = self._signals.columns[len(self._signals.columns) - 1]
        if start_time > last_day_in_data or end_time > last_day_in_data:
            raise DatetimeValidationException("Start time: year = {} month = {}, End time: year = {} month = {}. Input data: year = {} month = {}. Start time and end time must be within the date range of given data.".format(start_time.year, start_time.month, end_time.year, end_time.month, last_day_in_data.year, last_day_in_data.month))
