import pandas as pd
import datetime

class HistoricalSignalHelper(object):

    def read_and_store_historical_signals(self, input_data_file_path, sheet_name):

        excel_data = pd.read_excel(input_data_file_path, sheet_name = sheet_name, index = 0)
        # TODO: For now, drop the last row.
        #       Convert the index to multiple indices with hour, minute, and second.
        #       Or convert to Pandas.TimeDelta.
        excel_data = excel_data.drop(excel_data.index[len(excel_data.index) - 1])

        self._signals = excel_data

    def signals_in_range(self, start_time, end_time):

        beginning_of_the_day = pd.Timestamp(f"{start_time.year}-{start_time.month}-{start_time.day}")
        series_for_day = self._signals[beginning_of_the_day]
        series_in_range = series_for_day[datetime.time(start_time.hour, start_time.minute, start_time.second):datetime.time(end_time.hour, end_time.minute, end_time.second)]
        series_in_range_with_datetime_index = self._convert_index_to_datetime(series_in_range, start_time)
        return series_in_range_with_datetime_index.to_dict()

    @property
    def signals(self):
        return self._signals

    def _convert_index_to_datetime(self, series, start_time):
        index_list = series.index.tolist()
        datetime_index_list = [datetime.datetime.combine(start_time, index) for index in index_list]
        series.index = datetime_index_list
        return series
