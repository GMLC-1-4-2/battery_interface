# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from __future__ import absolute_import

import os
import json
import csv
from datetime import datetime, timedelta
from dateutil import parser

import utils
from weather_services.weather_service import WeatherService
from weather_services.points import PointEnum


class CsvWeatherService(WeatherService):
    """
    This class provides an example of pulling weather data from a CSV file
    """

    def __init__(self, *args, **kwargs):
        super(CsvWeatherService, self).__init__(*args, **kwargs)

    def get_data(self, zip_code, points, start_time, end_time, resolution):
        """
        This function queries data from a CSV data file.
        :param zip_code:
        :param points:
        :param start_time: datetime object
        :param end_time: datetime object
        :param resolution:
        :return: an array of dictionary. For example:
            [{'ts': datetime.datetime(2018, 1, 1, 8, 0), 'temperature': '72', 'relative_humidity': '50'},
            {'ts': datetime.datetime(2018, 1, 1, 9, 0), 'temperature': '73', 'relative_humidity': '49']
        """
        result = []
        weather_file_name = 'test_csv_weather.csv'
        weather_file_path = './csv_weather/' + weather_file_name

        reader = csv.DictReader(open(weather_file_path))

        # Let's reformat output to a standard format so others can use this csv service the same way as
        # other services (e.g., tmy3_weather_service)
        for row in reader:
            # Convert csv weather format to the standard format
            item = {
                PointEnum.ts: parser.parse(row['Timestamp']),
                PointEnum.temperature: row['Temp[F]'],
                PointEnum.relative_humidity: row['RH[%]']
            }

            # Push the converted item to the output list
            result.append(item)

        # NOTE: The 2 features below can be added later (similar to what has been done in tmy3_weather_service)
        # Slice data for interested time frame
        # Filter data for interested points

        return result

    @classmethod
    def pretty_print_result(cls, result, points):
        for rec in result:
            if len(points) == 0:
                print(rec)
            else:
                print(utils.format_timestamp(rec[PointEnum.ts]))
                for point in points:
                    print("{point}: {value}".format(point=point, value=rec[point]))
                print(os.linesep)


if __name__ == '__main__':
    weather_service = CsvWeatherService()

    print(os.linesep)
    print('Test: get_data')
    start_time = parser.parse("2018-01-01 08:00:00")
    end_time = parser.parse("2018-01-01 09:00:00")
    resolution = timedelta(minutes=15)
    points = []  # All points
    weather_data = weather_service.get_data('99352', points, start_time, end_time, resolution)
    weather_service.pretty_print_result(weather_data, points)
