# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from os.path import dirname, abspath, join
import os

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from dateutil import parser
from datetime import datetime, timedelta
import pandas as pd
import configparser
import numpy
import maya
import csv
from pathlib import Path

import utils
from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse
from fleet_config import FleetConfig
import matplotlib.pyplot as plt


class DistributionVoltageService:
    """
    The peak management service short summary
    """

    def __init__(self, *args, **kwargs):
    #def __init__(self, fleet, *args, **kwargs):
        # The scope of the project is to test service with one fleet...
        #self.fleet = fleet

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
        #self.drive_cycle = pd.read_csv(self.drive_cycle_file)
        self.drive_cycle = pd.read_csv(self.drive_cycle_file, parse_dates=['time'])
        self.Vupper = float(self.config.get(config_header, 'Vupper', fallback=1.035))
        self.Vlower = float(self.config.get(config_header, 'Vlower', fallback=0.965))
        self.operation_flag = self.config.get(config_header, 'operation_flag', fallback='0')
        #self.starttime = self.config.get(config_header, 'starttime')
        #self.endtime = self.config.get(config_header, 'endtime')

        #self.sim_step = timedelta(seconds=30)
        

    def request_loop(self, sensitivity_P = None, 
                     sensitivity_Q = None,
                     start_time = parser.parse("2017-08-01 16:00:00"),
                     end_time = parser.parse("2017-08-01 16:38:00")):
        # Sensitivity_P, Sensitivity_Q are values depending on feeder characteristics
        # We can use dummy value to conduct test
        #sensitivity_P = 0.001
        #sensitivity_Q = 0.005
        assigned_service_kW=self._fleet.assigned_service_kW()
        assigned_service_kVar=self._fleet.assigned_service_kW()
        
        if sensitivity_P==None:
            sensitivity_P=.05/assigned_service_kW
        if sensitivity_Q==None:
            sensitivity_Q=0.08/assigned_service_kVar
        


        cur_time = start_time
        #end_time = endtime

        delt = self.sim_step
        volt = self.drive_cycle["voltage"]
        time  = self.drive_cycle["time"]
        List_Time = list(time.values)
        dts = maya.parse(start_time).datetime() - maya.parse(List_Time[0]).datetime()
        dts = (dts).total_seconds()
        Vupper = self.Vupper
        Vlower = self.Vlower
        responses = []
        requests = []
        Voltage=[]
        while cur_time < end_time:
            # normal operation

            
            for n in range(len(list(time.values))):

                dta = maya.parse(List_Time[n]).datetime()  
                dtb = maya.parse(cur_time).datetime() - timedelta(seconds = dts)
                if dta==dtb:
                    index=n
              
            
           # index  = list(time.values).index(cur_time)
            cur_voltage = volt.values[index]
            Voltage.append(cur_voltage)
            #cur_voltage = 1.055
            if cur_voltage >= self.Vlower and cur_voltage <= self.Vupper:
                Prequest = 0
                Qrequest = 0
            else:
                if cur_voltage > Vupper:
                    dV = Vupper - cur_voltage
                    Qrequest  = dV/sensitivity_Q # need Q absorption
#                    if Qrequest<-1*assigned_service_kVar:
#                        Qrequest=-1*assigned_service_kVar
                    Prequest = dV/sensitivity_P # need P curtailment
#                    if Prequest<-1*assigned_service_kW:
#                        Prequest=-1*assigned_service_kW
                elif cur_voltage < Vlower:
                    dV = Vlower - cur_voltage
                    Qrequest = -dV/sensitivity_Q # need Q injection
#                    if Qrequest<assigned_service_kVar:
#                        Qrequest=-1*assigned_service_kVar
                    Prequest = -dV/sensitivity_P # need P injection
#                    if Prequest<assigned_service_kW:
#                        Prequest=-assigned_service_kW
                    
            fleet_request = FleetRequest(ts=cur_time,sim_step= delt, p=Prequest, q=Qrequest)
            fleet_response = self.fleet.process_request(fleet_request)
            responses.append(fleet_response)
            requests.append(fleet_request)
            cur_time += delt
            print("{}".format(cur_time))
            
        Qach = numpy.zeros((len(responses)))
        Pach = numpy.zeros((len(responses)))
        V_Up_limit = numpy.zeros((len(responses)))
        V_Down_Limit = numpy.zeros((len(responses)))
#            Time[idd]=res.ts
            
        ts_request = [r.ts for r in responses]
        Pach= [r.P_togrid for r in responses]
        Qach= [r.Q_togrid for r in responses]
        Pservice=[r.P_service for r in responses]
        Qservice=[r.Q_service for r in responses]
        Pbase=[r.P_base for r in responses]
        Qbase=[r.Q_base for r in responses]

        Pbase_Response=[r.P_base+r.P_service for r in responses]
        Qbase_Response=[r.Q_base+r.Q_service for r in responses]
        V_Up_limit=[Vupper for r in responses]
        V_Down_limit=[Vlower for r in responses]
        
        Preq=[r.P_req for r in requests]
        Qreq=[r.Q_req for r in requests]
            
        fig=plt.figure(1)
        plt.figure(figsize=(15, 8))
        plt.subplot(511)
        plt.plot(ts_request, Preq, label='P_Request')
        plt.plot(ts_request, Pservice, label='P_Response')
        plt.xlabel('Time')
        plt.ylabel('kW')
        #plt.title('Fleet Active Power')
        plt.legend(loc='lower right')
        
        plt.subplot(512)
        plt.plot(ts_request, Pbase_Response, label='P_base+P_Response')
        plt.plot(ts_request, Pach, label='P_togrid')
        plt.plot(ts_request, Pbase, label='P_base')
        plt.xlabel('Time')
        plt.ylabel('kW')
        #plt.title('Fleet Active Power')
        plt.legend(loc='lower right')        

        plt.subplot(513)
        plt.plot(ts_request, Qreq, label='Q_Request')
        plt.plot(ts_request, Qservice, label='Q_Response')
        plt.xlabel('Time')
        plt.ylabel('kVar')
        #plt.title('Fleet Active Power')
        plt.legend(loc='lower right')
        
        plt.subplot(514)
        plt.plot(ts_request, Qbase_Response, label='Q_base+Q_Response')
        plt.plot(ts_request, Qach, label='Q_togrid')
        plt.plot(ts_request, Qbase, label='Q_base')
        plt.xlabel('Time')
        plt.ylabel('kVar')
        #plt.title('Fleet Active Power')
        plt.legend(loc='lower right')    
        
        plt.subplot(515)
        plt.plot(ts_request, Voltage, label='Voltage')
        plt.plot(ts_request, V_Up_limit, label='upper limit')
#        plt.plot(ts_request, V_Down_Limit, label='Lower limit')
        plt.xlabel('Time')
        plt.ylabel('Volt')
        #plt.title('Fleet Active Power')
        plt.legend(loc='lower right')   
        
        
        data_folder=os.path.dirname(sys.modules['__main__'].__file__)
        plot_filename = datetime.now().strftime('%Y%m%d') + '_VoltageRegulation_FleetResponse_' + self.fleet.__class__.__name__  + '.png'
        File_Path_fig = join(data_folder, 'integration_test','voltage_regulation',plot_filename)

        plt.savefig(File_Path_fig, bbox_inches='tight')
#        File_Path_fig = os.path.join(self.base_path , 'VR_Fleet_Response.png')
#        fig.savefig(File_Path_fig)
        #plt.legend(loc='lower right')
        plt.close
        ServiceEefficacy=[]
        ValueProvided=[]
        ValueEfficacy=[]
 
        CSV_FileName=datetime.now().strftime('%Y%m%d') + '_Voltage_Regulation_' + self.fleet.__class__.__name__ + '.csv'

        data_folder=os.path.dirname(sys.modules['__main__'].__file__)
        File_Path_CSV = join(data_folder, 'integration_test','Voltage_Regulation',CSV_FileName)
        f = open(File_Path_CSV, "w")
        f.truncate()
        f.close()
        self.write_csv(File_Path_CSV,'Time','service efficacy (%)','value provided ($)','value efficacy (%)')
       
        for idd in range(len(Pach)):
            service_efficacy,value_provided,value_efficacy=self.calculation(Prequest=Preq[idd],
                                Qrequest=Qreq[idd],P0=Pservice[idd],Q0=Qservice[idd],price_P=1,price_Q=1)

            ServiceEefficacy.append(service_efficacy)
            ValueProvided.append(value_provided)
            ValueEfficacy.append(value_efficacy)
            
            self.write_csv(File_Path_CSV,ts_request[idd],service_efficacy,value_provided,value_efficacy)

#        fig, axs = plt.subplots(3, 1)
        fig=plt.figure(1)
        plt.figure(figsize=(15, 8))
        plt.subplot(311)
        plt.plot(ts_request, ServiceEefficacy, label='ServiceEefficacy')
        plt.xlabel('Time')
        plt.ylabel('%')
        plt.title('Service Metrics')
        plt.legend(loc='lower right')
        
        plt.subplot(312)
        plt.plot(ts_request, ValueProvided, label='ValueProvided')
        plt.xlabel('Time')
        plt.ylabel('$')
        
        plt.legend(loc='lower right')
        
        plt.subplot(313)
        plt.plot(ts_request, ValueEfficacy, label='ValueEfficacy')
        plt.xlabel('Time')
        plt.ylabel('%')
#        plt.title('Service Metrics')
        plt.legend(loc='lower right')
        
#        
#        axs[0].plot(ts_request, ServiceEefficacy)
#        axs[0].set_title('ServiceEefficacy')
#        #axs[0].set_xlabel('distance (m)')
#        axs[0].set_ylabel('%')
#        fig.suptitle('Service Metrics', fontsize=16)
#        
#        axs[1].plot(ts_request, ValueProvided)
#        #axs[1].set_xlabel('time (s)')
#        axs[1].set_title('ValueProvided')
#        axs[1].set_ylabel('$')
#        
#        axs[2].plot(ts_request, ValueEfficacy)
#        #axs[1].set_xlabel('time (s)')
#        axs[2].set_title('ValueEfficacy')
#        axs[2].set_ylabel('%')
        plot_filename = datetime.now().strftime('%Y%m%d') + '_VoltageRegulation_ServiceMetrics' + self.fleet.__class__.__name__  + '.png'
        File_Path_fig = join(data_folder, 'integration_test','voltage_regulation',plot_filename)

        plt.savefig(File_Path_fig, bbox_inches='tight')

        
        plt.show()    
            

    
        return [requests, responses]


    def autonomous_operation(self):
        # autonomous operation
        return self.drive_cycle

    def calculation(self,Prequest,Qrequest,P0,Q0,price_P,price_Q):
        # calculate generic metrics
        if Prequest==0:
            Prequest=0.0000001
        if Qrequest==0:
            Qrequest=0.0000001
        if isinstance(Q0, str) or Q0 == None:
            Q0 = 0
#        print('  Prequest = ' +repr(int(Prequest)) +'  Qrequest = ' +repr(int(Qrequest)) + '  P0 = ' +repr(int(P0)) +'  Q0 = ' +repr(int(Q0))) 
        
        service_efficacy = (P0/Prequest*100 + Q0/Qrequest*100)/2 # in %
        
        if Prequest==0.0000001 and Qrequest==0.0000001:
            if numpy.abs(service_efficacy)<.5:
                service_efficacy=100
            
        value_provided = numpy.abs(P0)*price_P + numpy.abs(Q0)*price_Q
        value_asked=numpy.abs(Prequest)*price_P+numpy.abs(Qrequest)*price_Q
        if value_asked==0:
            value_asked=0.0000001
#        print('  value_provided = ' +repr(int(value_provided)) +'  value_asked = ' +repr(int(value_asked)) ) 
        value_efficacy = value_provided*100/value_asked
        
        if value_asked==0.0000001 and numpy.abs(value_efficacy)<0.5:
            value_efficacy=100

        return [service_efficacy,value_provided,value_efficacy]

    def voltage_regulation_metrics(self,voltage_measure):
        # calculate voltage metrics
        # this metric calcualtion requires grid model simulation, can be added later

        return 1

    # Allow method "fleet" be used as an attribute.
    @property
    def fleet(self):
        return self._fleet

    # Inject the fleet into the service. Equivalent to adding "fleet" as a variable in __init__ at the beginning.
    @fleet.setter
    def fleet(self, value):
        self._fleet = value
        
    def write_csv(self,File_Path,ts_request,service_efficacy,value_provided,value_efficacy):     
        
        with open(File_Path, mode='a',newline='') as impact_metris:
            impact_metris_writer = csv.writer(impact_metris)
            impact_metris_writer.writerow([ts_request,service_efficacy,value_provided,value_efficacy])
