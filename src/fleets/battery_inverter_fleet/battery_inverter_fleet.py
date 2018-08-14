# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}
import sys
from os.path import dirname, abspath, join
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))

import configparser
from datetime import datetime, timedelta
import numpy  
import copy 
import math

from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse


class BatteryInverterFleet(FleetInterface):
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """

    def __init__(self, GridInfo, model_type="ERM", **kwargs):
        """
        Constructor
        """
        self.model_type = model_type
        config_header = self.model_type
        # establish the grid locations that the battery fleet is conected to
        self.grid = GridInfo
        # Get cur directory
        base_path = dirname(abspath(__file__))

        # Read config file
        self.config = configparser.ConfigParser()
        self.config.read(join(base_path, 'config.ini'))

        # Load config info with default values if there is no such config parameter in the config file
        self.name = self.config.get(config_header, 'Name', fallback='Battery Inverter Fleet')
        
        # Load different parameters for the energy reservoir model (ERM), or the charge reservoir model (CRM)
        if self.model_type == "ERM":
            self.max_power_charge = float(self.config.get(config_header, 'MaxPowerCharge', fallback=10))
            self.max_power_discharge = float(self.config.get(config_header, 'MaxPowerDischarge', fallback=10))
            self.max_apparent_power = float(self.config.get(config_header, 'MaxApparentPower', fallback=-10))
            self.min_pf = float(self.config.get(config_header, 'MinPF', fallback=0.8))
            self.max_soc = float(self.config.get(config_header, 'MaxSoC', fallback=100))
            self.min_soc = float(self.config.get(config_header, 'MinSoC', fallback=0))
            self.energy_capacity = float(self.config.get(config_header, 'EnergyCapacity', fallback=10))
            self.energy_efficiency = float(self.config.get(config_header, 'EnergyEfficiency', fallback=1))
            self.self_discharge_power = float(self.config.get(config_header, 'SelfDischargePower', fallback=0))
            self.max_ramp_up = float(self.config.get(config_header, 'MaxRampUp', fallback=10))
            self.max_ramp_down = float(self.config.get(config_header, 'MaxRampDown', fallback=10))
            self.num_of_devices = int(self.config.get(config_header, 'NumberOfDevices', fallback=1))
            Location_list = self.config.get(config_header, 'Locations', fallback=0)
            list_hold = Location_list.split(',')
            self.location = [int(e) for e in list_hold]
            # system states
            self.t = float(self.config.get(config_header, 't', fallback=10))
            self.soc = float(self.config.get(config_header, 'soc', fallback=10))
            self.cap = float(self.config.get(config_header, 'cap', fallback=10))
            self.maxp = float(self.config.get(config_header, 'maxp', fallback=10))
            self.minp = float(self.config.get(config_header, 'minp', fallback=10))
            self.maxp_fs = float(self.config.get(config_header, 'maxp_fs', fallback=10))
            self.rru = float(self.config.get(config_header, 'rru', fallback=10))
            self.rrd = float(self.config.get(config_header, 'rrd', fallback=10))
            self.ceff = float(self.config.get(config_header, 'ceff', fallback=10))
            self.deff = float(self.config.get(config_header, 'deff', fallback=10))
            self.P_req =float( self.config.get(config_header, 'P_req', fallback=10))
            self.Q_req = float(self.config.get(config_header, 'Q_req', fallback=10))
            self.P_service = float(self.config.get(config_header, 'P_service', fallback=0))
            self.Q_service = float(self.config.get(config_header, 'Q_service', fallback=0))
            self.P_service = float(self.config.get(config_header, 'P_service', fallback=0))
            self.Q_service = float(self.config.get(config_header, 'Q_service', fallback=0))
            self.es = float(self.config.get(config_header, 'es', fallback=10))
        
            self.fleet_model_type = self.config.get(config_header, 'FleetModelType', fallback='Uniform')
            if self.fleet_model_type == 'Uniform':
                self.soc = numpy.repeat(self.soc,self.num_of_devices)
            if self.fleet_model_type == 'Standard Normal SoC Distribution':
                self.soc_std = float(self.config.get(config_header, 'SOC_STD', fallback=0)) # Standard deveation of SoC spread
                self.soc = numpy.repeat(self.soc,self.num_of_devices) + self.soc_std * numpy.random.randn(self.num_of_devices) 
                for i in range(self.num_of_devices):
                    if self.soc[i] > self.max_soc:
                        self.soc[i] = self.max_soc
                    if self.soc[i] < self.min_soc:
                        self.soc[i] = self.min_soc
            self.P_service = numpy.repeat(self.P_service,self.num_of_devices)
            self.Q_service = numpy.repeat(self.Q_service,self.num_of_devices)
        elif self.model_type == "CRM":
            self.energy_capacity = float(self.config.get(config_header, 'EnergyCapacity', fallback=10))
            # inverter parameters
            self.inv_name = self.config.get(config_header, 'InvName', fallback='Name')
            self.inv_type = self.config.get(config_header, 'InvType', fallback='Not Defined')
            self.coeff_0 = float(self.config.get(config_header, 'Coeff0', fallback=0))
            self.coeff_1 = float(self.config.get(config_header, 'Coeff1', fallback=1))
            self.coeff_2 = float(self.config.get(config_header, 'Coeff2', fallback=0))
            self.max_power_charge = float(self.config.get(config_header, 'MaxPowerCharge', fallback=10))
            self.max_power_discharge = float(self.config.get(config_header, 'MaxPowerDischarge', fallback=-10))
            self.max_apparent_power = float(self.config.get(config_header, 'MaxApparentPower', fallback=-10))
            self.min_pf = float(self.config.get(config_header, 'MinPF', fallback=0.8))
            self.max_ramp_up = float(self.config.get(config_header, 'MaxRampUp', fallback=10))
            self.max_ramp_down = float(self.config.get(config_header, 'MaxRampDown', fallback=10))
            # battery parameters
            self.bat_name = self.config.get(config_header, 'BatName', fallback='Name')
            self.bat_type = self.config.get(config_header, 'BatType', fallback='Not Defined')
            self.n_cells = float(self.config.get(config_header, 'NCells', fallback=10))
            self.voc_model_type = self.config.get(config_header, 'VOCModelType', fallback='Linear')
            if self.voc_model_type == 'Linear': # note all model values assume SoC ranges from 0% to 100%
                self.voc_model_m = float(self.config.get(config_header, 'VOC_Model_M', fallback=0.005))
                self.voc_model_b = float(self.config.get(config_header, 'VOC_Model_b', fallback=1.8))
            if self.voc_model_type == 'Quadratic':
                self.voc_model_a = float(self.config.get(config_header, 'VOC_Model_A', fallback=0.005))
                self.voc_model_b = float(self.config.get(config_header, 'VOC_Model_B', fallback=1.8))
                self.voc_model_c = float(self.config.get(config_header, 'VOC_Model_C', fallback=1.8))
            if self.voc_model_type == 'Cubic':
                self.voc_model_a = float(self.config.get(config_header, 'VOC_Model_A', fallback=0.005))
                self.voc_model_b = float(self.config.get(config_header, 'VOC_Model_B', fallback=1.8))
                self.voc_model_c = float(self.config.get(config_header, 'VOC_Model_C', fallback=1.8))
                self.voc_model_d = float(self.config.get(config_header, 'VOC_Model_D', fallback=1.8))
            if self.voc_model_type == 'CubicSpline':
                SoC_list = self.config.get(config_header, 'VOC_Model_SOC_LIST', fallback=0.005)
                list_hold = SoC_list.split(',')
                self.voc_model_SoC_list = [float(e) for e in list_hold]
                a_list = self.config.get(config_header, 'VOC_Model_A', fallback=0.005)
                b_list = self.config.get(config_header, 'VOC_Model_B', fallback=0.005)
                c_list = self.config.get(config_header, 'VOC_Model_C', fallback=0.005)
                d_list = self.config.get(config_header, 'VOC_Model_D', fallback=0.005)
                list_hold = a_list.split(',')
                self.voc_model_a = [float(e) for e in list_hold]
                list_hold = b_list.split(',')
                self.voc_model_b = [float(e) for e in list_hold]
                list_hold = c_list.split(',')
                self.voc_model_c = [float(e) for e in list_hold]
                list_hold = d_list.split(',')
                self.voc_model_d = [float(e) for e in list_hold]
            self.max_current_charge = float(self.config.get(config_header, 'MaxCurrentCharge', fallback=10))
            self.max_current_discharge = float(self.config.get(config_header, 'MaxCurrentDischarge', fallback=-10))
            self.max_voltage = float(self.config.get(config_header, 'MaxVoltage', fallback=58))
            self.min_voltage= float(self.config.get(config_header, 'MinVoltage', fallback=48))
            self.max_soc = float(self.config.get(config_header, 'MaxSoC', fallback=100))
            self.min_soc = float(self.config.get(config_header, 'MinSoC', fallback=0))
            self.charge_capacity = float(self.config.get(config_header, 'ChargeCapacity', fallback=10))
            self.coulombic_efficiency = float(self.config.get(config_header, 'CoulombicEfficiency', fallback=1))
            self.self_discharge_current = float(self.config.get(config_header, 'SelfDischargeCurrent', fallback=0))
            self.r0 = float(self.config.get(config_header, 'R0', fallback=0))
            self.r1 = float(self.config.get(config_header, 'R1', fallback=0))
            self.r2 = float(self.config.get(config_header, 'R2', fallback=0))
            self.c1 = float(self.config.get(config_header, 'C1', fallback=0))
            self.c2 = float(self.config.get(config_header, 'C2', fallback=0))
            # fleet parameters
            self.num_of_devices = int(self.config.get(config_header, 'NumberOfDevices', fallback=10))
            Location_list = self.config.get(config_header, 'Locations', fallback=0)
            list_hold = Location_list.split(',')
            self.location = [int(e) for e in list_hold]
            # battery system states
            self.t = float(self.config.get(config_header, 't', fallback=0))
            self.soc = float(self.config.get(config_header, 'soc', fallback=50))
            self.v1 = float(self.config.get(config_header, 'v1', fallback=0))
            self.v2 = float(self.config.get(config_header, 'v2', fallback=0))
            self.voc = float(self.config.get(config_header, 'voc', fallback=53))
            self.vbat = float(self.config.get(config_header, 'vbat', fallback=53))
            self.ibat = float(self.config.get(config_header, 'ibat', fallback=0))
            self.pdc = float(self.config.get(config_header, 'pdc', fallback=0))
            self.cap = float(self.config.get(config_header, 'cap', fallback=10.6))
            self.maxp = float(self.config.get(config_header, 'maxp', fallback=10))
            self.minp = float(self.config.get(config_header, 'minp', fallback=-10))
            self.maxp_fs = float(self.config.get(config_header, 'maxp_fs', fallback=0))
            self.rru = float(self.config.get(config_header, 'rru', fallback=10))
            self.rrd = float(self.config.get(config_header, 'rrd', fallback=-10))
            self.ceff = float(self.config.get(config_header, 'ceff', fallback=1))
            self.deff = float(self.config.get(config_header, 'deff', fallback=1))
            self.P_req = float(self.config.get(config_header, 'P_req', fallback=0))
            self.Q_req = float(self.config.get(config_header, 'Q_req', fallback=0))
            self.P_service = float(self.config.get(config_header, 'P_service', fallback=0))
            self.Q_service = float(self.config.get(config_header, 'Q_service', fallback=0))
            self.P_service = float(self.config.get(config_header, 'P_service', fallback=0))
            self.Q_service = float(self.config.get(config_header, 'Q_service', fallback=0))
            self.es = float(self.config.get(config_header, 'es', fallback=5.3))
            self.fleet_model_type = self.config.get(config_header, 'FleetModelType', fallback='Uniform')
            if self.fleet_model_type == 'Uniform':
                self.soc = numpy.repeat(self.soc,self.num_of_devices)
            if self.fleet_model_type == 'Standard Normal SoC Distribution':
                self.soc_std = float(self.config.get(config_header, 'SOC_STD', fallback=0)) # Standard deveation of SoC spread
                self.soc = numpy.repeat(self.soc,self.num_of_devices) + self.soc_std * numpy.random.randn(self.num_of_devices) 
                for i in range(self.num_of_devices):
                    if self.soc[i] > self.max_soc:
                        self.soc[i] = self.max_soc
                    if self.soc[i] < self.min_soc:
                        self.soc[i] = self.min_soc
            self.v1 = numpy.repeat(self.v1,self.num_of_devices)
            self.v2 = numpy.repeat(self.v2,self.num_of_devices)
            self.voc = numpy.repeat(self.voc,self.num_of_devices)
            self.vbat = numpy.repeat(self.vbat,self.num_of_devices)
            self.ibat = numpy.repeat(self.ibat,self.num_of_devices)
            self.pdc = numpy.repeat(self.pdc,self.num_of_devices)
            self.maxp = numpy.repeat(self.maxp,self.num_of_devices)
            self.minp = numpy.repeat(self.minp,self.num_of_devices)
            self.P_service = numpy.repeat(self.P_service,self.num_of_devices)
            self.Q_service = numpy.repeat(self.Q_service,self.num_of_devices)
        else: 
            print('Error: ModelType not selected as either energy reservoir model (self), or charge reservoir model (self)')
            print('Battery-Inverter model config unable to continue. In config.ini, set ModelType to self or self')
        
        # fleet configuration variables
        self.is_P_priority = bool(self.config.get('FW', 'is_P_priority', fallback=True))
        self.is_autonomous = bool(self.config.get('FW', 'is_autonomous', fallback=False))
        self.autonomous_threshold = self.config.get('FW', 'autonomous_threshold', fallback='None')

        # autonomous operation
        self.FW21_Enabled = bool(self.config.get('FW', 'FW21_Enabled', fallback=False))
        self.VV11_Enabled = bool(self.config.get('VV', 'VV11_Enabled', fallback=False))
        if self.FW21_Enabled == True:
            GFreq_list = self.config.get('FW', 'GFreq', fallback=0.005)
            GP_list = self.config.get('FW', 'GP', fallback=0.005)
            CFreq_list = self.config.get('FW', 'CFreq', fallback=0.005)
            CP_list = self.config.get('FW', 'CP', fallback=0.005)
            list_hold = GFreq_list.split(',')
            self.GFreq = [float(e) for e in list_hold]
            list_hold = GP_list.split(',')
            self.GP = [float(e) for e in list_hold]
            list_hold = CFreq_list.split(',')
            self.CFreq = [float(e) for e in list_hold]
            list_hold = CP_list.split(',')
            self.CP = [float(e) for e in list_hold]
        if self.VV11_Enabled == True:
            Vset_list = self.config.get('VV', 'Vset', fallback=0.005)
            Qset_list = self.config.get('VV', 'Qset', fallback=0.005)
            list_hold = Vset_list.split(',')
            self.Vset = [float(e) for e in list_hold]
            list_hold = Qset_list.split(',')
            self.Qset = [float(e) for e in list_hold]

    def process_request(self, fleet_request):
        """
        This function takes the fleet request and repackages it for the interal run function
        :param fleet_request: an instance of FleetRequest
        :return fleet_response: an instance of FleetResponse
        """
        ts = fleet_request.ts_req
        dt = fleet_request.sim_step
        p_req = fleet_request.P_req
        q_req = fleet_request.Q_req

        # call run function with proper inputs
        fleet_response = self.run(p_req, q_req,ts, dt)

        return fleet_response

    def frequency_watt(self, p_req = 0,ts=datetime.utcnow(),location=0):
        """
        This function takes the requested power, date, time, and location
        and modifys the requested power according to the configured FW21 
        :param p_req: real power requested, ts:datetime opject,
               location: numerical designation for the location of the BESS
        :return p_mod: modifyed real power based on FW21 function
        """
        f = self.grid.get_frequency(ts,location)
        n = len(self.GFreq)
        k = len(self.CFreq)
        pmin = self.GP[0]
        pmax = self.CP[0]
        p_mod = copy.copy(p_req)
        for i in range(n-1):
            if f>self.GFreq[i] and f<self.GFreq[i+1] :
                m =  (self.GP[i] - self.GP[i+1]) / (self.GFreq[i] - self.GFreq[i+1]) 
                pmin = self.GP[i] + m * (f - self.GFreq[i])
        if f>self.GFreq[n-1]:
            pmin = self.GP[n-1]
        for i in range(k-1):
            if f>self.CFreq[i] and f<self.CFreq[i+1] :
                m =  (self.CP[i] - self.CP[i+1]) / (self.CFreq[i] - self.CFreq[i+1]) 
                pmax = self.CP[i] + m * (f - self.CFreq[i]) 
        if f>self.CFreq[k-1]:   
            pmax = self.CP[k-1]
        if p_req>pmax  :
            p_mod=pmax
        if p_req<pmin  :
            p_mod=pmin   
        return p_mod

    def volt_var(self, ts=datetime.utcnow(),location=0):
        '''
        This function takes the date, time, and location of the BESS
        and returns a reactive power set point according to the configured VV11 function
        :param ts:datetime opject, location: numerical designation for the location of the BESS
        :return q_req: reactive power set point based on FW21 function
        '''
        v = self.grid.get_voltage(ts,location)
        n = len(self.Vset)
        q_req = self.Qset[0]
        for i in range(n-1):
            if v>self.Vset[i] and v<self.Vset[i+1] :
                m =  (self.Qset[i] - self.Qset[i+1]) / (self.Vset[i] - self.Vset[i+1]) 
                q_req = self.Qset[i] + m * (v - self.Vset[i])
        return q_req

    def run(self, P_req=[0], Q_req=[0],ts=datetime.utcnow(), del_t=timedelta(hours=1)):
        '''
        This function takes the real and reactive power requested, date, time, and time step and 
        calculates the updated fleet variables as well as a FleetResponse object based on what the 
        simulated fleet is able to provide. It does this by dividing up the requests and sending each 
        device in the fleet its own request. If some of the fleet is unable to supply the requested 
        power, then the remainder is devided umung the remaining devices. 
        :param P_req: requested real power, Q_req: requested reactive power
               ts:datetime opject, del_t: timedelta object
        :return  fleet_response: an instance of FleetResponse 
        '''
        np = numpy.ones(self.num_of_devices,int)
        nq = numpy.ones(self.num_of_devices,int)
        p_none = 0
        q_none = 0
        if P_req==None:
            P_req = 0
            p_req = 0
            p_none = 1
        else:
            p_req = P_req/self.num_of_devices
        if Q_req==None:
            Q_req = 0
            q_req = 0
            q_none = 1
        else:
            q_req = Q_req/self.num_of_devices
        p_tot = 0.0
        q_tot = 0.0
        dt = del_t.total_seconds() / 3600.0 
        self.t = self.t + dt

        p_FW = numpy.zeros(self.num_of_devices,float)
        q_VV = numpy.zeros(self.num_of_devices,float)
        
        response = FleetResponse()
        response.ts = ts
        
        last_P = numpy.zeros(self.num_of_devices,int)
        last_Q = numpy.zeros(self.num_of_devices,int)
        soc_update = copy.copy(self.soc)
        if self.model_type == 'CRM':
            pdc_update = self.pdc
            ibat_update = self.ibat
            v1_update = self.v1
            v2_update = self.v2
            vbat_update = self.vbat

        for i in range(self.num_of_devices):
            last_P[i] = self.P_service[i]
            last_Q[i] = self.Q_service[i]
            self.P_service[i] = 0
            self.Q_service[i] = 0
        TOL = 0.000001  # tolerance 
        one_pass = 1 #guarantees at least one pass through the control loop
        while ((p_tot < P_req-TOL or p_tot > P_req+TOL) or (q_tot < Q_req-TOL or q_tot > Q_req+TOL)) and sum(np)!=0 and sum(nq)!=0 or one_pass == 1: #continue looping through devices until the power needs are met or all devices are at their limits
            one_pass = 0
            # distribute the requested power equally among the devices that are not at their limits
            p_req = (P_req - p_tot)/sum(np)
            q_req = (Q_req - q_tot)/sum(nq) 
            for i in range(self.num_of_devices):
                if self.model_type == 'ERM':
                    soc_update[i] = self.run_soc_update(p_req,q_req,np,nq,last_P,last_Q,i,dt)
                if self.model_type == 'CRM':
                    [soc_update[i],pdc_update[i],ibat_update[i],vbat_update[i],v1_update[i],v2_update[i]] = \
                         self.run_soc_update(p_req,q_req,np,nq,last_P,last_Q,i,dt)
            # at the end of looping through the devices, add up their power to determine if the request has been met
            p_tot = sum(self.P_service)
            q_tot = sum(self.Q_service)
        
        # after all the power needs have been placed and met, then make adjustments based on autonomous operation settings 
        if (self.FW21_Enabled == True or self.VV11_Enabled == True) and self.is_autonomous == True:
            for i in range(self.num_of_devices) :
                p_req = self.P_service[i]
                q_req = self.Q_service[i]
                # determin if VV11 or FW21 change the p_req or q_req
                if self.FW21_Enabled == True:
                    p_mod = self.frequency_watt(p_req,ts,self.location[i])
                if self.VV11_Enabled == True:
                    if q_none == 1:
                        q_mod = self.volt_var(ts,self.location[i])
                    if self.model_type == 'ERM':
                        soc_update[i] = self.run_soc_update(p_req=(p_mod-p_req),q_req=(q_mod-q_req),np=numpy.ones(self.num_of_devices),nq=numpy.ones(self.num_of_devices),last_P=last_P,last_Q=last_Q,i=i,dt=dt)
                    if self.model_type == 'CRM':
                        [soc_update[i],pdc_update[i],ibat_update[i],vbat_update[i],v1_update[i],v2_update[i]] = \
                            self.run_soc_update(p_req=(p_mod-p_req),q_req=(q_mod-q_req),np=numpy.ones(self.num_of_devices),nq=numpy.ones(self.num_of_devices),last_P=last_P,last_Q=last_Q,i=i,dt=dt)
                else :
                    if self.model_type == 'ERM':
                        soc_update[i] = self.run_soc_update(p_req=(p_req),q_req=(q_req),np=numpy.ones(self.num_of_devices),nq=numpy.ones(self.num_of_devices),last_P=last_P,last_Q=last_Q,i=i,dt=dt)
                    if self.model_type == 'CRM':
                        [soc_update[i],pdc_update[i],ibat_update[i],vbat_update[i],v1_update[i],v2_update[i]] = \
                            self.run_soc_update(p_req=p_req,q_req=q_req,np=numpy.ones(self.num_of_devices),nq=numpy.ones(self.num_of_devices),last_P=last_P,last_Q=last_Q,i=i,dt=dt)

        p_tot = sum(self.P_service)
        q_tot = sum(self.Q_service)    
        # update SoC
        self.soc = soc_update
        if self.model_type == 'CRM':
            self.v1 = v1_update
            self.v2 = v2_update
            self.voc_update()
            self.ibat = ibat_update
            self.vbat = (self.v1 + self.v2 + self.voc + self.ibat*self.r0) *self.n_cells
        # once the power request has been met, or all devices are at their limits, return the response variables
        response.P_service = p_tot
        response.Q_service = q_tot  
        response.soc = numpy.average(self.soc)
        response.E = numpy.average(self.soc) * self.energy_capacity / 100.0
        return response 
    
    def run_soc_update(self,p_req=0,q_req=0,np=1,nq=1,last_P=0,last_Q=0,i=0,dt=1):
        '''
        This function is used by the run function to calculate the fleet state variable updates
        for each device. 
        '''
        if np[i] == 1 or nq[i] == 1:
            #  Max ramp rate and apparent power limit checking
            if np[i] == 1 :
                p_ach = self.P_service[i] + p_req
                if (p_ach-last_P[i]) > self.max_ramp_up:
                    p_ach = self.max_ramp_up + last_P[i]
                    np[i] = 0
                elif (p_ach-last_P[i]) < self.max_ramp_down:
                    p_ach = self.max_ramp_down + last_P[i]
                    np[i] = 0
                    
                if p_ach < self.max_power_discharge:
                    p_ach  = self.max_power_discharge
                    np[i] = 0
                if p_ach > self.max_power_charge:
                    p_ach = self.max_power_charge
                    np[i] = 0
            else:
                p_ach = self.P_service[i] 

            if nq[i] == 1:
                q_ach = self.Q_service[i] + q_req
                if (q_ach-last_Q[i]) > self.max_ramp_up:
                    q_ach = self.max_ramp_up + last_Q[i]
                    nq[i] = 0
                elif (q_ach-last_Q[i]) < self.max_ramp_down:
                    q_ach = self.max_ramp_down + last_Q[i]
                    nq[i] = 0
            else:
                q_ach = self.Q_service[i] 
            
            S_req = float(numpy.sqrt(p_ach**2 + q_ach**2))
            
            # watt priority
            if self.is_P_priority == True:
                if S_req > self.max_apparent_power:
                    q_ach = float(numpy.sqrt(numpy.abs(self.max_apparent_power**2 - p_ach**2)) * numpy.sign(q_ach))
                    S_req = self.max_apparent_power
            else: # var priority
                if S_req > self.max_apparent_power:
                    p_ach = float(numpy.sqrt(numpy.abs(self.max_apparent_power**2 - q_ach**2)) * numpy.sign(p_ach))
                    S_req = self.max_apparent_power 
            # check power factor limit
            if p_ach != 0.0: 
                if float(numpy.abs(S_req/p_ach)) < self.min_pf:
                    q_ach =  float(numpy.sqrt(numpy.abs((p_ach/self.min_pf)**2 - p_ach**2)) * numpy.sign(q_ach))
            if np[i] == 1:
                # run function for ERM model type
                if self.model_type == 'ERM':
                    # Calculate SoC_update and Power Achieved
                    Ppos = min(self.max_power_charge, max(p_ach, 0))
                    Pneg = max(self.max_power_discharge, min(p_ach, 0))
                    soc_update = self.soc[i] + float(100) * dt * (Pneg + (
                        Ppos * self.energy_efficiency) + self.self_discharge_power) / self.energy_capacity
                    if soc_update > self.max_soc:
                        Ppos = (self.energy_capacity * (self.max_soc - self.soc[i]) / (
                            float(100) * dt) - self.self_discharge_power) / self.energy_efficiency
                        soc_update = self.max_soc
                        np[i] = 0
                    if soc_update < self.min_soc:
                        Pneg = self.energy_capacity * (self.min_soc - self.soc[i]) / (
                            float(100) * dt) - self.self_discharge_power
                        soc_update = self.min_soc
                        np[i] = 0                                    

                    p_ach = (Ppos + Pneg)
                    q_ach =  q_ach
                    self.P_service[i] = p_ach
                    self.Q_service[i] = q_ach
                    return  soc_update
                # run function for CRM model type
                elif self.model_type == 'CRM':
                    # convert AC power p_ach to DC power pdc
                    pdc_update = self.coeff_2*(p_ach**2)+self.coeff_1*(p_ach)+self.coeff_0 

                    # convert DC power pdc to DC current
                    b = ((self.v1[i] + self.v2[i]+ self.voc[i])*self.n_cells) 
                    a = self.r0 * self.n_cells 
                    c = -pdc_update * 1000
                    ibat_update = (-b+numpy.sqrt(b**2 - 4*a*c))/(2*a)
                    
                    # calculate dynamic voltages
                    v1_update = self.v1[i] + dt *( (1/(self.r1*self.c1))*self.v1[i] + (1/(self.c1))*ibat_update)
                    v2_update = self.v2[i] + dt *( (1/(self.r2*self.c2))*self.v2[i] + (1/(self.c2))*ibat_update)
                    vbat_update = (v1_update  + v2_update + self.voc[i] + ibat_update*self.r0) *self.n_cells

                    # Calculate SoC and Power Achieved
                    Ipos = min(self.max_current_charge, max(ibat_update, 0))
                    Ineg = max(self.max_current_discharge, min(ibat_update, 0))
                    soc_update = self.soc[i] + float(100) * dt * (Ineg + (
                        Ipos * self.coulombic_efficiency) + self.self_discharge_current) / self.charge_capacity
                    if soc_update > self.max_soc:
                        Ipos = self.charge_capacity *((self.max_soc - self.soc[i] )/ (float(100) * dt) - self.self_discharge_current) / self.coulombic_efficiency
                        soc_update = self.max_soc
                        np[i] = 0
                        pdc_update  = Ipos *vbat_update / 1000
                        if self.coeff_2 != 0:
                            p_ach = (-self.coeff_1 +float(numpy.sqrt(self.coeff_1**2 - 4*self.coeff_2*(self.coeff_0-pdc_update))))/(2*self.coeff_2)
                        else: 
                            p_ach  = (pdc_update[i] - self.coeff_0)/self.coeff_1
                    if soc_update < self.min_soc:
                        Ineg = self.charge_capacity * (self.min_soc - self.soc[i]) / (
                            float(100) * dt) - self.self_discharge_current
                        soc_update = self.min_soc
                        np[i] = 0                                    
                        pdc_update  = Ineg *vbat_update / 1000
                        if self.coeff_2 != 0:
                            p_ach = (-self.coeff_1 +float(numpy.sqrt(self.coeff_1**2 - 4*self.coeff_2*(self.coeff_0-pdc_update))))/(2*self.coeff_2)
                        else: 
                            p_ach  = (pdc_update - self.coeff_0)/self.coeff_1
                    
                    ibat_update = Ipos + Ineg
                    v1_update = self.v1[i] + dt *( (1/(self.r1*self.c1))*self.v1[i] + (1/(self.c1))*ibat_update)
                    v2_update = self.v2[i] + dt *( (1/(self.r2*self.c2))*self.v2[i] + (1/(self.c2))*ibat_update)
                    vbat_update = (v1_update  + v2_update + self.voc[i] + ibat_update*self.r0) *self.n_cells
                    self.P_service[i] = p_ach
                    self.Q_service[i] = q_ach
                    return  [soc_update, pdc_update, ibat_update, vbat_update, v1_update, v2_update]
        

    def voc_update(self): 
        '''
        This function updates the open-circuit-voltage (voc) state variable based on what type of 
        fit has been configured into the CRM. NOTE: the CubicSline option is configured to use
        MATLAB's 'spline' function to calculate the diferent coefficients and SoC list. 
        NOTE: The coefficients assume VOC based on SOC in [0,1] rather than SOC in [0,100] as
        is used everywhere else in this code. This is only for conviniance based on previously 
        fit data sets and can be changed easily by changeing the scaling factor below from 100 to 1. 
        '''
        s = self.soc/100
        for i in range(self.num_of_devices):
            if self.voc_model_type== "Linear":
                self.voc[i] = self.voc_model_m*s[i] + self.voc_model_b
            elif self.voc_model_type == "Quadratic":
                self.voc[i] = self.voc_model_a*(s[i]**2) + self.voc_model_b*s[i] + self.voc_model_c
            elif self.voc_model_type == "Cubic":
                self.voc[i] = self.voc_model_a*(s[i]**3) + self.voc_model_b*(s[i]**2) + self.voc_model_c*s[i] + self.voc_model_d
            elif self.voc_model_type == "CubicSpline":
                j = 0
                for s_cnt in self.voc_model_SoC_list:
                    if s[i] > s_cnt:
                        j = j + 1
                self.voc[i] = self.voc_model_a[j-1]*((s[i]-self.voc_model_SoC_list[j-1])**3) \
                            + self.voc_model_b[j-1]*((s[i]-self.voc_model_SoC_list[j-1])**2) \
                            + self.voc_model_c[j-1]*(s[i]-self.voc_model_SoC_list[j-1]) \
                            + self.voc_model_d[j-1]
            else:
                print('Error: open circuit voltage (voc) model type (voc_model_type) is not defined properly')
                print('in config_self.ini set VocModelType=Linear or =CubicSpline')
            pass

    def voc_query(self,SOC):
        '''
        This function chexks the open-circuit-voltage (voc) state variable based on what type of 
        fit has been configured into the CRM. Unlike voc_update, this function does not change the 
        self.voc state variable. NOTE: the CubicSline option is configured to use
        MATLAB's 'spline' function to calculate the diferent coefficients and SoC list. 
        The coefficients assume VOC based on SOC in [0,1] rather than SOC in [0,100] as
        is used everywhere else in this code. This is only for conviniance based on previously 
        fit data sets and can be changed easily by changeing the scaling factor below from 100 to 1. 
        ''' 
        SOC = SOC/100
        if self.voc_model_type== "Linear":
            VOC = self.voc_model_m*SOC + self.voc_model_b
        elif self.voc_model_type == "Quadratic":
            VOC = self.voc_model_a*(SOC**2) + self.voc_model_b*SOC + self.voc_model_c
        elif self.voc_model_type == "Cubic":
            VOC = self.voc_model_a*(SOC**3) + self.voc_model_b*(SOC**2) + self.voc_model_c*SOC + self.voc_model_d
        elif self.voc_model_type == "CubicSpline":
            j = 0
            for s_cnt in self.voc_model_SoC_list:
                if SOC > s_cnt:
                    j = j + 1
            VOC = self.voc_model_a[j-1]*((SOC-self.voc_model_SoC_list[j-1])**3) \
                        + self.voc_model_b[j-1]*((SOC-self.voc_model_SoC_list[j-1])**2) \
                        + self.voc_model_c[j-1]*(SOC-self.voc_model_SoC_list[j-1]) \
                        + self.voc_model_d[j-1]
        else:
            print('Error: open circuit voltage (voc) model type (voc_model_type) is not defined properly')
            print('in config_self.ini set VocModelType=Linear or =CubicSpline')
        return VOC

    def cost(self, initSoC = 50,finSoC = 50,del_t=timedelta(hours=1)):
        '''
        This function is for use in dynamic programing optimization and round trip efficiency calculation. 
        :param initSoC: starting state-of-charge, finSoC: final state-of-charge
                del_t: time between initail and fial states of charge
        :return Power: power required to move the average fleet SoC initSoC to finSoC in del_t
                Cost: Currently not used but is a placeholder for an internal battery degredation based cost
                Able: returns 1 if the the transision from initSoC to finSoC is posible in del_t 
                      returnd 0 otherwise
        '''
        # pre-define variables
        Cost = 0
        Able = 1
        Power = 0
        dt = del_t.total_seconds() / 3600.0 
        # impose SoC constraints
        if initSoC > self.max_soc:
            Able = 0
        if initSoC < self.min_soc:
            Able = 0
        if finSoC > self.max_soc:
            Able = 0
        if finSoC < self.min_soc:
            Able = 0

        if self.model_type == 'ERM':
            DSoC = finSoC - initSoC
            if DSoC >= 0:
                Power = ((self.energy_capacity * DSoC / (float(100)*dt)) - self.self_discharge_power)/self.energy_efficiency
            if DSoC < 0:
                Power = (self.energy_capacity * DSoC / (float(100)*dt)) - self.self_discharge_power
            # linear power cost function
        #     Cost = Power*0.01
            # quadratic power cost function
        #     Cost = Power*Power*0.01
            Ppos = max(Power,0)
            Pneg = min(Power,0)
            # inpose power constraints
            if Ppos > self.max_power_charge:
                Able = 0
                Power = 0
            if Pneg < self.max_power_discharge:
                Able = 0
                Power = 0
        if self.model_type == 'CRM':
            Current = 0
            DSoC = finSoC - initSoC
            # Calculate battery current
            if DSoC >= 0:
                Current = ((self.charge_capacity * DSoC / (float(100)*dt)) - self.self_discharge_current)/self.coulombic_efficiency
            if DSoC < 0:
                Current = ((self.charge_capacity * DSoC / (float(100)*dt)) - self.self_discharge_current)
            Voltage = (Current*self.r0+((self.voc_query(initSoC)+self.voc_query(finSoC))/2))
            PowerDC =  self.n_cells*Current*(Voltage)/1000
            if self.coeff_2 != 0:
                Power = (-self.coeff_1 +float(numpy.sqrt(self.coeff_1**2 - 4*self.coeff_2*(self.coeff_0-PowerDC))))/(2*self.coeff_2)
                if math.isnan(Power):
                    Power  = (PowerDC - self.coeff_0)/self.coeff_1
            else: 
                Power  = (PowerDC - self.coeff_0)/self.coeff_1

            Ipos = max(Current,0)
            Ineg = min(Current,0)
            # impose current limites
            if Ipos > self.max_current_charge:
                Able = 0
                Power = 0
                Current = 0
            if Ineg < self.max_current_discharge:
                Able = 0
                Power = 0
                Current = 0
            # impose voltage limites
            if Voltage > self.max_voltage:
                Voltage = self.max_voltage
                Able = 0
                Power = 0
                Current = 0
            if Voltage < self.min_voltage:
                Voltage = self.min_voltage
                Able = 0
                Power = 0
                Current = 0 
                
            Ppos = max(Power,0)
            Pneg = min(Power,0)
            # impose power limits
            if Ppos > self.max_power_charge:
                Able = 0
                Power = 0
                Current = 0
            if Pneg < self.max_power_discharge:
                Able = 0
                Power = 0
                Current = 0

        Power = Power*self.num_of_devices
        Cost = 0 #Power*self.num_of_devices
        return [Power,Cost,Able]

    def forecast(self, requests):
        """
        This function repackages the list of fleet requests passed to it into the interal run function.
        Inorder for this to be a forecast, and therfore not change the state variables of the fleet, the 
        fleets state variables are saved before calling the run function and then the states are restored
        to their initial values after the forecast simulation is complete.
        :param fleet_requests: list of fleet requests
        :return res: list of service responses
        """
        responses = []
        SOC = self.soc 

        if self.model_type == 'ERM':
            # Iterate and process each request in fleet_requests
            for req in requests:
                FleetResponse = self.run(req.P_req,req.Q_req ,req.sim_step)
                res = FleetResponse
                responses.append(res)
            # reset the model
            self.soc = SOC 
            
        elif self.model_type == 'CRM':
            PDC = self.pdc 
            IBAT = self.ibat
            VBAT = self.vbat
            V1 = self.v1
            V2 = self.v2
            VOC = self.voc 
            ES = self.es
            # Iterate and process each request in fleet_requests
            for req in requests:
                FleetResponse = self.run(req.P_req,req.Q_req,req.ts_req,req.sim_step)
                res = FleetResponse
                responses.append(res)
            # reset the model
            self.soc = SOC 
            self.pdc = PDC
            self.ibat = IBAT
            self.vbat = VBAT
            self.v1 = V1
            self.v2 = V2
            self.voc = VOC
            self.es = ES
        else: 
            print('Error: ModelType not selected as either energy reservoir model (self), or charge reservoir model (self)')
            print('Battery-Inverter model forecast is unable to continue. In config.ini, set ModelType to self or self')

        return responses

    def change_config(self, fleet_config):
        """
        This function updates the fleet configuration settings programatically.
        :param fleet_config: an instance of FleetConfig
        """

        # change config
        self.is_P_priority = fleet_config.is_P_priority
        self.is_autonomous = fleet_config.is_autonomous
        self.autonomous_threshold = fleet_config.autonomous_threshold

        pass

