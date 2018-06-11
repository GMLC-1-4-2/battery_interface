# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import os
import json
import sqlite3
from datetime import datetime, timedelta
from dateutil import parser

import utils
from weather_services.weather_service import WeatherService
from weather_services.points import PointEnum
from weather_services.epw_record import EpwRecord


class Tmy3WeatherService(WeatherService):
    """
    This class provides weather data from TMY3 data files
    """

    def __init__(self, *args, **kwargs):
        super(Tmy3WeatherService, self).__init__(*args, **kwargs)

    def get_data(self, zip_code, points, start_time, end_time, resolution):
        """
        This function queries data from a TMY3 data file.
        :param zip_code:
        :param points:
        :param start_time: datetime object with a dummy year value
        :param end_time: datetime object with a dummy year value
        :param resolution:
        :return: an array of dictionary. For example:
            [{'ts': datetime.datetime(2018, 1, 1, 8, 0), 'temperature': '72', 'relative_humidity': '50'},
            {'ts': datetime.datetime(2018, 1, 1, 9, 0), 'temperature': '73', 'relative_humidity': '49']

        Note:
            - start_time and end_time has to be in the same year
        """
        result = []
        weather_file_name = self.get_weather_file_name(zip_code)
        weather_file_path = './tmy3/' + weather_file_name

        # Extract tmy3 data to result
        if end_time > start_time and weather_file is not None:
            tmy_data = []
            # Extract data from weather file
            tmy_start_time = None
            tmy_end_time = None
            with open(weather_file_path, 'r') as f:
                lines = f.readlines()
                for i in range(len(lines)):
                    if i > 7:
                        values = lines[i].split(',')
                        epw_rec = EpwRecord(values)
                        # Filter out records outside of interested time range
                        tmy_start_time = datetime(epw_rec.year, start_time.month, start_time.day,
                                                  start_time.hour, start_time.minute)
                        tmy_end_time = datetime(epw_rec.year, end_time.month, end_time.day,
                                                end_time.hour, end_time.minute)

                        # Ignore if the record is before start time
                        if epw_rec.ts < tmy_start_time:
                            continue

                        # Break if the record is after end time (it's because tmy3 files are sorted by datetime)
                        if epw_rec.ts > tmy_end_time:
                            break

                        tmy_data.append(epw_rec)

            # Return if no data
            if len(tmy_data) == 0:
                return result

            # Interpolate if needed
            # Example: temp & rel_hum
            # start_values = [82, 20]
            # end_values = [84, 25]
            interpolated_data = []
            if resolution < timedelta(hours=1):
                for i in range(len(tmy_data)-1):
                    interpolated = self.lin_interpolate(tmy_data[i].ts,
                                                        tmy_data[i+1].ts,
                                                        tmy_data[i].to_array_for_calculation(),
                                                        tmy_data[i+1].to_array_for_calculation(),
                                                        resolution)
                    # Interpolation result includes start & end
                    # Discard the last interpolated item if this is not the last tmy_data item
                    if i < len(tmy_data)-2:
                        interpolated_data.extend(interpolated[:-1])

                    # Include the last interpolated imte if this is the last tmy_data item
                    else:
                        interpolated_data.extend(interpolated)

            # Convert interpolated_data to tmy3_epw
            tmy3_epw_data = []
            for item in interpolated_data:
                values = [item[0].year, item[0].month, item[0].day, item[0].hour+1, item[0].minute,
                          tmy_data[0].data_source]
                values.extend(item[1])
                epw_rec = EpwRecord(values)
                tmy3_epw_data.append(epw_rec)

            # Filtered out unnecessary points and reformat final result
            for rec in tmy3_epw_data:
                # No point = all points
                if len(points) == 0:
                    json_obj = self.json_2_obj(rec)
                    result.append(json_obj)

                # Just select interested point
                else:
                    json_obj = self.json_2_obj(rec)
                    item = {
                        PointEnum.ts: json_obj[PointEnum.ts]
                    }
                    for point in points:
                        item[point] = json_obj[point]
                    result.append(item)

        return result

    def get_weather_file_name(self, zip_code):
        weather_file = None

        # Query weather file from weather info database
        con = sqlite3.connect('./tmy3/tmy3.db')
        with con:
            # Query based on zip_code
            cur = con.cursor()
            cur.execute("SELECT Weather_File_Name FROM tmy3 WHERE Zip_Code={zip_code}".format(zip_code=zip_code))

            # Get the 1st weather file
            data = cur.fetchall()
            for rec in data:
                weather_file = rec[0]
                break

        return weather_file

    def json_2_obj(cls, epw_record):
        json_str = epw_record.to_json()
        json_obj = json.loads(json_str)
        if PointEnum.ts in json_obj:
            json_obj[PointEnum.ts] = parser.parse(json_obj[PointEnum.ts])

        return json_obj

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
    # Test zip code for Tri-cities
    print('Test: get_weather_file')
    weather_service = Tmy3WeatherService()
    weather_file = weather_service.get_weather_file_name('99352')
    if weather_file is None:
        print('No weather file found')
    else:
        print(weather_file)

    print(weather_service.get_weather_file_name('99354'))

    print(os.linesep)
    print('Test: get_data 1 hours')
    start_time = parser.parse("2000-05-01 12:00:00")
    end_time = parser.parse("2000-05-01 13:00:00")
    resolution = timedelta(minutes=15)
    points = []
    weather_data = weather_service.get_data('99352', points, start_time, end_time, resolution)
    weather_service.pretty_print_result(weather_data, points)

    print(os.linesep)
    print('Test: get_data 2 hours')
    start_time = parser.parse("2000-05-01 12:00:00")
    end_time = parser.parse("2000-05-01 14:00:00")
    resolution = timedelta(minutes=15)
    points = []
    weather_data = weather_service.get_data('99352', points, start_time, end_time, resolution)
    weather_service.pretty_print_result(weather_data, points)

    print(os.linesep)
    print('Test: get_data 1 day')
    start_time = parser.parse("2000-05-01 12:00:00")
    end_time = parser.parse("2000-05-02 12:00:00")
    resolution = timedelta(minutes=15)
    points = [PointEnum.relative_humidity, PointEnum.dry_bulb, PointEnum.dew_point]
    weather_data = weather_service.get_data('99352', points, start_time, end_time, resolution)
    weather_service.pretty_print_result(weather_data, points)
