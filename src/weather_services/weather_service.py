# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from datetime import datetime, timedelta


class WeatherService():
    """
    This class provides skeleton for weather services
    """

    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, zip_code, points, start_time, end_time, resolution):
        pass

    def get_forecast(self, zip_code, points, start_time, end_time, resolution):
        pass

    def get_current(self, zip_code, points):
        pass

    def lin_interpolate(self, start_time, end_time, start_values, end_values, resolution):
        """
        Linear interpolation: the input order in start_values and end_values are preserved.
            Assumption for simplicity:
                - (end_time - start_time) is multiple of resolution
                - start_values has the same items as end_values
        :param start_time: datetime
        :param end_time: datetime
        :param start_value: an array of values
        :param end_value: an array of values
        :param resolution: timedelta
        :return: an array of [(time1, [values1]), (time2, values2)] tuples including start_time to end_time values

        Note: this is default implementation. Derived classes may want to override this
        """

        result = [(start_time, start_values)]
        num_steps = (end_time - start_time)/resolution
        num_steps = int(num_steps)
        cur_step = 1
        t = start_time + resolution
        while cur_step < num_steps:
            values = []
            for i in range(len(start_values)):
                delta = (end_values[i] - start_values[i]) * cur_step / num_steps
                values.append(start_values[i] + delta)
            result.append((t, values))
            t += resolution
            cur_step += 1

        result.append((end_time, end_values))

        return result


if __name__ == '__main__':
    from datetime import timedelta
    from dateutil import parser

    # Interpolate temp & rh with 15-min resolution
    ws = WeatherService()

    start_time = parser.parse("2018-05-01 12:00:00")
    end_time = parser.parse("2018-05-01 13:00:00")
    start_values = [82, 20]
    end_values = [84, 26]

    resolution = timedelta(minutes=15)
    result = ws.lin_interpolate(start_time, end_time, start_values, end_values, resolution)

    print(result)
