# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from dateutil import parser
from datetime import datetime, timedelta
import pandas as pd
import configparser

import utils
from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse
from fleet_config import FleetConfig


class DistributionVoltageService:
    """
    The peak management service short summary
    """

    def __init__(self, fleet, *args, **kwargs):
        # The scope of the project is to test service with one fleet...
        self.fleet = fleet

        # Get cur directory
        self.base_path = dirname(abspath(__file__))

        # Read config file
        config_header = 'config'
        self.config = configparser.ConfigParser()
        self.config.read(join(self.base_path, 'config.ini'))

        self.name = self.config.get(config_header, 'name', fallback='Distribution Voltage Regulation Service')
        self.capacity_scaling_factor = float(self.config.get(config_header, 'capacity_scaling_factor', fallback=1.0))
        #self.f_reduction = float(self.config.get(config_header, 'f_reduction', fallback=0.1))
        self.drive_cycle_file = self.config.get(config_header, 'drive_cycle_file',
                                                fallback='drive.cycle.voltage.csv')
        self.drive_cycle_file = join(self.base_path, 'data', self.drive_cycle_file)
        self.drive_cycle = pd.read_csv(self.drive_cycle_file)
        self.Vupper = float(self.config.get(config_header, 'Vupper', fallback=1.05))
        self.Vlower = float(self.config.get(config_header, 'Vlower', fallback=0.95))
        self.operation_flag = self.config.get(config_header, 'operation_flag', fallback='0')
        self.starttime = self.config.get(config_header, 'starttime')
        self.endtime = self.config.get(config_header, 'endtime')

        self.sim_step = timedelta(seconds=30)

    def request_loop(self, sensitivity_P, sensitivity_Q):
        # Sensitivity_P, Sensitivity_Q are values depending on feeder characteristics
        # We can use dummy value to conduct test
        sensitivity_P = 0.001
        sensitivity_Q = 0.005
        cur_time = self.starttime
        end_time = self.endtime
        delt = self.sim_step
        volt = self.drive_cycle["voltage"]
        time  = self.drive_cycle["time"]
        Vupper = self.Vupper
        Vlower = self.Vlower
        responses = []
        requests = []
        while cur_time < end_time:
            # normal operation
            index  = list(time.values).index(cur_time)
            cur_voltage = volt.values[index]
            if cur_voltage >= self.Vlower and cur_voltage <= self.Vupper:
                Prequest = 0
                Qrequest = 0
            else:
                if cur_voltage > Vupper:
                    dV = Vupper - cur_voltage
                    Qrequest  = -dV/sensitivity_Q # need Q absorption
                    Prequest = -dV/sensitivity_P # need P curtailment
                elif cur_voltage < Vlower:
                    dV = Vlower - cur_voltage
                    Qrequest = dV/sensitivity_Q # need Q injection
                    Prequest = dV/sensitivity_P # need P injection

            fleet_request = FleetRequest(cur_time, delt, Prequest, Qrequest)
            fleet_response = self.fleet_device.process_request(fleet_request)
            responses.append(fleet_response)
            requests.append(fleet_request)
            cur_time += delt

        return [requests, responses]

    def autonomous_operation(self):
        # autonomous operation
        return self.drive_cycle

    def calculation(self,Prequest,Qrequest,P0,Q0,price_P,price_Q):
        # calculate generic metrics
        service_efficacy = (P0/Prequest_pre*100 + Q0/Qrequest_pre)/2 # in %
        value_provided = P0*price_P + Q0*price_Q
        value_efficacy = value_provided/(Prequest_pre*price_P+Qrequest_pre*price_Q)

        return [service_efficacy,value_provided,value_efficacy]

    def voltage_regulation_metrics(self,voltage_measure):
        # calculate voltage metrics
        # this metric calcualtion requires grid model simulation, can be added later

        return 1
