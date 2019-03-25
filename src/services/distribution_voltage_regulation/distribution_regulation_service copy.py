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

    def request_loop(self, P0, Q0, sensitivity_P, sensitivity_Q):
        cur_time = self.starttime
        end_time = self.endtime
        delt = self.sim_step
        volt = self.drive_cycle["voltage"]
        while cur_time < end_time:
            # normal operation
            
            Pmax = P_forecast[0]
            Pmin = P_forecast[1]
            Qmax = Q_forecast[0]
            Qmin = Q_forecast[1]
            if volt >= self.Vlower and volt <= self.Vupper:
                dP = 0
                dQ = 0
            else:
                if volt > self.Vupper:
                    dV = self.Vupper - volt
                elif volt < self.Vlower:
                    dV = self.Vlower - volt
                if Qmax > 0: # if the fleet can provide Q, use Q as priority
                    dQ = dV/sensitivity_Q
                    if Q0+dQ<=Qmax and Q0+dQ>=Qmin:
                        dP = 0 # no need to change P
                    else:
                        if Q0+dQ > Qmax:
                            dQ = Qmax - Q0
                        elif Q0+dQ < Qmin:
                            dQ = Qmin-Q0
                        dP = (dV-sensitivity_Q*dQ)/sensitivity_P
                else:
                    # if the fleet can only provide P
                    dP = dV/sensitivity_P

                if dP:
                    if dP+P0 > Pmax:
                        dP = Pmax - P0
                    elif dP+P0 < Pmin:
                        dP = Pmin - P0

            Prequest = P0 + dP
            Qrequest = Q0 + dQ


            fleet_request = FleetRequest(cur_time, delt)
            fleet_response = self.fleet_device.process_request(fleet_request)
            responses.append(fleet_response)
            cur_time += delt
            # print("{}".format(cur_time))

        return responses

    def request(self,P0,): # added input variables; what's the purpose of sim_step??
        fleet_request = FleetRequest(ts=ts, sim_step=sim_step, p=p, q=0.0)
        print("Processing request at timestep %s" % ts)
        fleet_response = self.fleet.process_request(fleet_request)
        #print(fleet_response.P_service)
        return fleet_request, fleet_response


    def normal_operation(self,P_forecast,Q_forecast,P0,Q0,sensitivity_P,sensitivity_Q):
        # normal operation
        volt = self.drive_cycle["voltage"]
        Pmax = P_forecast[0]
        Pmin = P_forecast[1]
        Qmax = Q_forecast[0]
        Qmin = Q_forecast[1]
        if volt >= self.Vlower and volt <= self.Vupper:
            dP = 0
            dQ = 0
        else:
            if volt > self.Vupper:
                dV = self.Vupper - volt
            elif volt < self.Vlower:
                dV = self.Vlower - volt
            if Qmax > 0: # if the fleet can provide Q, use Q as priority
                dQ = dV/sensitivity_Q
                if Q0+dQ<=Qmax and Q0+dQ>=Qmin:
                    dP = 0 # no need to change P
                else:
                    if Q0+dQ > Qmax:
                        dQ = Qmax - Q0
                    elif Q0+dQ < Qmin:
                        dQ = Qmin-Q0
                    dP = (dV-sensitivity_Q*dQ)/sensitivity_P
            else:
                # if the fleet can only provide P
                dP = dV/sensitivity_P

            if dP:
                if dP+P0 > Pmax:
                    dP = Pmax - P0
                elif dP+P0 < Pmin:
                    dP = Pmin - P0

        Prequest = P0 + dP
        Qrequest = Q0 + dQ

        return [Prequest,Qrequest]




    def autonomous_operation(self):
        # autonomous operation
        return self.drive_cycle

    def generic_metrics_calculation(self,Prequest_pre,Qrequest_pre,P0,Q0,price_P,price_Q):
        # calculate generic metrics
        service_efficacy = (P0/Prequest_pre*100 + Q0/Qrequest_pre)/2 # in %
        value_provided = P0*price_P + Q0*price_Q
        value_efficacy = value_provided/(Prequest_pre*price_P+Qrequest_pre*price_Q)

        return [service_efficacy,value_provided,value_efficacy]


    def voltage_regulation_metrics(self,voltage_measure):
        # calculate voltage metrics
        # this metric calcualtion requires grid model simulation, can be added later

        return 1



service = DistributionVoltageService('PV')
service.run_fleet_forecast_test()