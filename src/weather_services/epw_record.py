from datetime import datetime
import utils

class EpwRecord:
    def __init__(self, values):
        """
        Create an object corresponding to a row in an epw tmy3 file
        :param values: an array of values in the same order as in epw files
        """
        self.from_array(values)

    def from_array(self, values):
        self.year = int(values[0])
        self.month = int(values[1])
        self.day = int(values[2])
        self.hour = int(values[3])
        self.minute = int(values[4])
        self.data_source = values[5]
        self.dry_bulb = float(values[6])  # Dry Bulb Temperature {C}
        self.dew_point = float(values[7])  # Dew Point Temperature {C}
        self.relative_humidity = float(values[8])  # Relative Humidity {%}
        self.pressure = float(values[9])  # Atmospheric Pressure {Pa}
        self.horizontal_radiation = float(values[10])  # Extraterrestrial Horizontal Radiation {Wh/m2}
        self.normal_radiation = float(values[11])  # Extraterrestrial Direct Normal Radiation {Wh/m2}
        self.sky_radiation = float(values[12])  # Horizontal Infrared Radiation Intensity from Sky {Wh/m2}
        self.global_horizontal_radiation = float(values[13])  # Global Horizontal Radiation {Wh/m2}
        self.direct_normal_radiation = float(values[14])  # Direct Normal Radiation {Wh/m2}
        self.diffuse_horizontal_radiation = float(values[15])  # Diffuse Horizontal Radiation {Wh/m2}
        self.global_horizontal_illumination = float(values[16])  # Global Horizontal Illuminance {lux}
        self.direct_normal_illumination = float(values[17])  # Direct Normal Illuminance {lux}
        self.diffuse_horizontal_illumination = float(values[18])  # Diffuse Horizontal Illuminance {lux}
        self.zenith_illumination = float(values[19])  # Zenith Luminance {Cd/m2}
        self.wind_direction = float(values[20])  # Wind Direction {deg}
        self.wind_speed = float(values[21])  # Wind Speed {m/s}
        self.total_sky_cover = float(values[22])  # Total Sky Cover {.1}
        self.opaque_sky_cover = float(values[23])  # Opaque Sky Cover {.1}
        self.visibility = float(values[24])  # Visibility {km}
        self.ceil_height = float(values[25])  # Ceiling Height {m}
        self.weather_observation = float(values[26])  # Present Weather Observation
        self.weather_codes = float(values[27])  # Present Weather Codes
        self.precipitation_water = float(values[28])  # Precipitable Water {mm}
        self.aerosol_optical_depth = float(values[29])  # Aerosol Optical Depth {.001}
        self.snow_depth = float(values[30])  # Snow Depth {cm}
        self.days_last_snow = float(values[31])  # Days Since Last Snow
        self.albedo = float(values[32])  # Albedo {.01}
        self.rain = float(values[33])  # Liquid Precipitation Depth {mm}
        self.rain_quantity = float(values[34])  # Liquid Precipitation Quantity {hr}

        self.ts = datetime(self.year, self.month, self.day, self.hour-1, self.minute)

    def to_array_for_calculation(self):
        return [self.dry_bulb, self.dew_point, self.relative_humidity, self.pressure,
                self.horizontal_radiation, self.normal_radiation, self.sky_radiation,
                self.global_horizontal_radiation, self.direct_normal_radiation, self.diffuse_horizontal_radiation,
                self.global_horizontal_illumination, self.direct_normal_illumination,
                self.diffuse_horizontal_illumination, self.zenith_illumination,
                self.wind_direction, self.wind_speed,
                self.total_sky_cover, self.opaque_sky_cover,
                self.visibility, self.ceil_height,
                self.weather_observation, self.weather_codes,
                self.precipitation_water, self.aerosol_optical_depth,
                self.snow_depth, self.days_last_snow, self.albedo,
                self.rain, self.rain_quantity]

    def to_json(self):
        import json

        return json.dumps(self, default=lambda o: o.__dict__ if type(o) is not datetime else utils.format_timestamp(o))


if __name__ == '__main__':
    epw = EpwRecord([2000,1,1,1,0,'?9?9?9?9E0?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9*9*9?9*9*9',
                     -2.0,-2.0,100,99700,0,0,250,0,0,0,0,0,0,0,0,0.0,6,3,8.0,77777,9,
                     999999999,100,0.0510,0,88,0.400,999.0,99.0])
    print(epw.to_json())
