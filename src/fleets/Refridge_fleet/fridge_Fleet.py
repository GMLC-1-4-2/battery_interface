# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 15:07:49 2018
For GMLC 1.4.2, fleet Virtual Battery Model for Commercail Refridgeration Systems
Based on a valided RC case thermal model

Last update: 05/09/2019
Version: 1.0

@author: Jin Dong (ORNL), Teja Kuruganti (ORNL)
"""

# code needed for GLOBAL fleet_interface
import sys
from os.path import dirname, abspath, join
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))
################################################################

from configparser import ConfigParser
from datetime import datetime, timedelta

from fleets.Refridge_fleet.case_model import CaseModel
from fleets.Refridge_fleet.case_model import AC_RF

from fleet_interface import FleetInterface
from fleet_response import FleetResponse
from fleets.Refridge_fleet.load_config import LoadConfig
from frequency_droop import FrequencyDroop

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import random
import pandas as pd
import scipy as sp
import time
import csv
from utils import ensure_ddir

class RFFleet(FleetInterface):   #FleetInterface
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """
    def __init__(self, GridInfo, ts, s_step):  # add , sim_step later
        """
        for battery def __init__(self, GridInfo,**kwargs):
        old: (self, Steps = 100, Timestep = 10, P_request = 0, Q_request = 0, forecast = 0, StartHr = 40)
        ts: Timestamp in simulation loop: datetime
        sim_step: Simulation time step: timedelta object
        """
        # Location of working path
        base_path = dirname(abspath(__file__))
        
        # Read config file
        config = ConfigParser()
        config.read(join(base_path, 'config.ini'))
       
        # Load config file and store data in a dataframe
        LC = LoadConfig(config)
        self.df_RFModels = LC.get_config_models()
        
        # Run baseline power to store baseline power and SOC if parameters 
        # of the fleet are changed. ONLY ASSIGN TRUE IF YOU CHANGE THE 
        # PARAMETERS OF THE FLEET AS IT WILL DRAMATICALLY INCREASE THE CPU TIME
        self.run_baseline = LC.get_run_baseline()
        # Establish the properties of the grid on which the fleet is connected on
        self.grid = GridInfo
        # Get cur directory
        base_path = dirname(abspath(__file__))

        # Total number of RFs
        self.numRF = self.df_RFModels['Total_RFs'].sum()

        #INPUTS
        self.shortcycle=3*60 # Shortcycle minimum time (minutes) that unit has to stay off before turning back on
        self.minrun=1*60 # minutes minimum runtime for unit

        " TODO: update this sim_step in main interface "
        self.sim_step = s_step.total_seconds() # load sim_step from main call
		# self.sim_step = 1 * 60 # 1 min in seconds
       
        self.shortcycle_ts=int(round(self.shortcycle/self.sim_step,0))  #number of time steps during short cycle timer
        self.minrun_ts=int(round(self.minrun/self.sim_step,0))

        self.Tset = 6.0 #Celsius  cooling set point
        self.deadband = 2 #Celsius cooling dead band
            
        # #%% Frequency-watt parameters
        # FrequencyWatt='Frequency Watt'
        # self.db_UF=float(LC.get(FW,'db_UF'))
        # self.db_OF=float(LC.get(FW,'db_OF'))
        # self.k_UF=float(self.config.get(FrequencyWatt,'k_UF'))
        # self.k_OF=float(self.config.get(FrequencyWatt,'k_OF'))

        # generate random houses based on the validated building model
        # varying R, C values by some coefficients
        # represents low efficiency, normal efficiency and high efficiency houses (corresponding to different envelope/insulation parameters)
        # for envelope type, location and max. number of service calls need to specify discrete values and randomly sampled to get a desired distribution 
        # self.numRF = 60 # number of RFs in fleet, default 50

        # How to calculate effective fleet rating: this is going to be poorly
        # met because it does not consider random availability of the fleet. 
        # However this seems to be the best approximation
		
        self.numRF = int(self.numRF)
        self.fleet_rating = (self.numRF * 5)  # unit power is 5 kw, approximate 25% can provide service   

        # Weight used to scale the service request
        self.service_weight = LC.get_service_weight()    

        """
        Can this fleet operate in autonomous operation?
        """
        
        # Locations of the subfleets: suppose that you only have one location
        self.location = np.random.randint(0,1,self.numRF)
        
        # Fleet configuration variables
        self.is_P_priority = LC.get_fleet_config()[0]
        self.is_autonomous = LC.get_fleet_config()[1]
        
        # Autonomous operation
        fw_21 = LC.get_FW()
        self.FW21_Enabled = fw_21[0]
        if self.FW21_Enabled == True:
            # Single-sided deadband value for low-frequency, in Hz
            self.db_UF = fw_21[1]
            # Single-sided deadband value for high-frequency, in Hz
            self.db_OF = fw_21[2]
            # Per-unit frequency change corresponding to 1 per-unit power output change (frequency droop), dimensionless
            self.k_UF  = fw_21[3]
            # Per-unit frequency change corresponding to 1 per-unit power output change (frequency droop), dimensionless
            self.k_OF  = fw_21[4]
            # Available active power, in p.u. of the DER rating
            self.P_avl = fw_21[5]
            # Minimum active power output due to DER prime mover constraints, in p.u. of the DER rating
            self.P_min = fw_21[6]
            self.P_pre = fw_21[7]
            
            # Randomization of discrete devices: deadbands must be randomize to provide a continuous response
            self.db_UF_subfleet = np.random.uniform(low = self.db_UF[0], high = self.db_UF[1], size = (self.numRF, ))
            self.db_OF_subfleet = np.random.uniform(low = self.db_OF[0], high = self.db_OF[1], size = (self.numRF, ))
        
        # Impact metrics of the fleet
        metrics = LC.get_impact_metrics_params()
        # Aveage indoor temperature baseline
        self.ave_TairB = metrics[0]
        # Aveage indoor temperature baseline
        self.ave_Tair = metrics[1]
		# Cylces in baseline
        self.cycle_basee = metrics[2]
        # Cylces in grid operation
        self.cycle_grid = metrics[3]
		# State of Charge of the battery equivalent model
        self.SOCb_metric = metrics[4]
		# State of Charge of the battery equivalent model
        self.SOC_metric = metrics[5]
        # Unmet hours of the fleet
        self.unmet_hours = metrics[6]

        # P_togrid/P_baseline
        self.ratio_P_togrid_P_base = 1.
        # Energy impacts of providing the grid service
        self.energy_impacts = 0.
       
        ########### initial indoor temperatures and SoC
        self.TairInitialMean = 5.5 #deg C
        self.TairInitialStddev = 0.3 #deg C

        self.TfoodInitialMean = 6.11 #deg C
        self.TfoodInitialStddev = 0.3 #deg C

        self.TcaseInitialMean = 3.5 #deg C
        self.TcaseInitialStddev = 0.3 #deg C
        
        # initial temperature setpoints
        self.TsetInitialMean = 6 #deg C  convert from 80F+-4
        self.TsetInitialStddev = 1   #2.22 #deg C
        
        self.minSOC = 0.1 # minimum SoC for aggregator to call for shed service
        self.maxSOC = 0.9 # minimum SoC for aggregator to call for add service
        
        self.minCapacityAdd = 150 #W-hr, minimum add capacity to be eligible for add service
        self.minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
     
        # Varying parameters for different Diaplay cases
                
        # R value of infiltration
        self.R_infilMasterList = [0.008341, 0.008341, 0.008341, 0.008341, 0.008341, 0.006673,  0.006673,
                  0.006673, 0.010009, 0.010009]   # K/W 50% Normal, 30% Low-product (*0.8), 20% High-product (*1.2)
        # R value of case
        self.R_caseMasterList = [0.044077, 0.044077, 0.044077, 0.044077, 0.044077, 0.035262,
                    0.035262, 0.035262,  0.052892, 0.052892] # K/W 50% Normal, 30% Low-efficiency (*0.8), 20% High-efficiency (*1.2)
        # R value of food
        self.R_foodMasterList = [0.004614, 0.004614, 0.004614, 0.004614, 0.004614,
                   0.003691, 0.003691, 0.003691, 0.005538, 0.005538]  # K/W 50% Normal, 30% Low-efficiency (*0.8), 20% High-efficiency (*1.2)
        
        # C value of air
        self.C_airMasterList = [111053, 111053, 111053, 111053, 111053, 88842,  88842,
                  88842, 133263, 133263]   # J/K 50% Normal, 30% Low-product, 20% High-product

        # C value of food
        self.C_foodMasterList = [2844769, 2844769, 2844769, 2844769, 2844769, 2275815,  2275815,
                  2275815, 3413722, 3413722]   # J/K 50% Normal, 30% Low-product, 20% High-product
        
        # C value of case
        self.C_caseMasterList = [10200510, 10200510, 10200510, 10200510, 10200510, 8160408,  8160408,
                  8160408, 12240162, 12240162]   # J/K 50% Normal, 30% Low-product (*0.8), 20% High-product (*1.2)

        #  Typical US nationwide climate locations
        # self.ClimateMasterList = ['Miami', 'Phoenix', 'Atlanta', 'Atlanta', 'Las Vegas', 'Denver',  
        #                      'Denver', 'Atlanta', 'Miami', 'Minneapolis'] # 20% Miami
        # # 30% Atlanta; 20% Denver, 10% for Phoneix, Vegas and Minneapolis

        self.ClimateMasterList = ['Atlanta', 'Atlanta', 'Atlanta', 'Atlanta', 'Atlanta', 'Atlanta',  
                             'Atlanta', 'Atlanta', 'Atlanta', 'Atlanta'] # For consistant baseline, fix to one climate
        
        self.MaxServiceCallMasterList = [30, 20, 20, 10, 15, 25, 5, 15, 30] # this is the max number of monthly service calls for load add/shed.
        
         ########################################################################
        
        # Initialize timestamps and local times of the class for future calculations
        self.initial_ts = ts # time stamp to start the simulation
        self.ts = ts
        self.initial_time = self.get_time_of_the_day(ts)
        self.time = self.get_time_of_the_day(ts)
        self.dt = 1       # time step (in seconds)

        ##################################     
        #    Initializing lists to be saved to track indivisual RF performance over each timestep

        # Randomly set up and mix the RF fleet
        # Random seed for regenerating the same result
        self.seed = 0
        np.random.seed(self.seed)

        # generate distribution of initial Refridge fleet states. 

        self.TairInitialB=np.random.normal(self.TairInitialMean, self.TairInitialStddev,self.numRF)
        self.TfoodInitialB=np.random.normal(self.TfoodInitialMean, self.TfoodInitialStddev,self.numRF)
        self.TcaseInitialB=np.random.normal(self.TcaseInitialMean, self.TcaseInitialStddev,self.numRF)
		
        self.TairInitial=np.random.normal(self.TairInitialMean, self.TairInitialStddev,self.numRF)
        self.TfoodInitial=np.random.normal(self.TfoodInitialMean, self.TfoodInitialStddev,self.numRF)
        self.TcaseInitial=np.random.normal(self.TcaseInitialMean, self.TcaseInitialStddev,self.numRF)
        
        # random Temperature setpoints
        self.TsetInitial=np.random.normal(self.TsetInitialMean, self.TsetInitialStddev,self.numRF)
        
        # sampling from houses with different sizes of display cases
        self.R_case = [random.choice(self.R_caseMasterList) for n in range(self.numRF)]
        self.R_food = [random.choice(self.R_foodMasterList) for n in range(self.numRF)]
        self.R_infil = [random.choice(self.R_infilMasterList) for n in range(self.numRF)]
		
        self.C_food = [random.choice(self.C_foodMasterList) for n in range(self.numRF)]
        self.C_air = [random.choice(self.C_airMasterList) for n in range(self.numRF)]
        self.C_case = [random.choice(self.C_caseMasterList) for n in range(self.numRF)]

        self.Location = [random.choice(self.ClimateMasterList) for n in range(self.numRF)]
        
        self.MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numRF)]    
        
        ###########################################################################       
                
        Tamb = []
        for a in range(self.numRF):             
      
            (tamb) = get_daily_conditions(self.Location[a], self.sim_step, self.ts)  # location, timestep_s, start_time            

            Tamb.append(tamb)

        self.Tamb = np.array(Tamb)              

        self.AvailableCapacityAdd = [0 for x in range(self.numRF)]
        self.AvailableCapacityShed = [0 for x in range(self.numRF)]
        self.ServiceCallsAccepted = [0 for x in range(self.numRF)]
        self.ServiceProvided = [0 for x in range(self.numRF)]
 	
        self.IsAvailableAdd = np.random.randint(2, size=self.numRF+1)
        self.IsAvailableShed = np.random.randint(2, size=self.numRF+1)

        self.elementOnB = np.random.randint(2, size=self.numRF)
        self.elementOn = np.random.randint(2, size=self.numRF)

        self.lockonB = [self.minrun+1 for x in range(self.numRF)]
        self.lockoffB = [self.shortcycle+1 for x in range(self.numRF)]
        self.lockon = [self.minrun+1 for x in range(self.numRF)]
        self.lockoff = [self.shortcycle+1 for x in range(self.numRF)]
		
        self.cycle_off_base = [0 for x in range(self.numRF)]
        self.cycle_on_base = [0 for x in range(self.numRF)]
        self.cycle_off_grid = [0 for x in range(self.numRF)]
        self.cycle_on_grid = [0 for x in range(self.numRF)] 
        
        # MaxServiceAddedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]
        # MaxServiceShedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]

        self.TotalServiceCallsAcceptedperRF = [0 for y in range(self.numRF)]    
   
        self.SoCInit = [0.8 for y in range(self.numRF)]
        self.SOC = self.SoCInit
        self.SOCb = self.SoCInit

        self.AvailableCapacityAddInit = [0 for y in range(self.numRF)]
        self.AvailableCapacityShedInit = [0 for y in range(self.numRF)]

        self.IsAvailableAddInit = np.random.randint(2, size=self.numRF+1)
        self.IsAvailableShedInit = np.random.randint(2, size=self.numRF+1)
        
        self.step = 0

        ##############################################################################################################
 
        #    Initializing the Refridge models
        #    Get the baseline power
        self.RFs = [CaseModel(self.Tamb[0], self.TsetInitial[number], self.R_case[number], self.R_food[number], self.R_infil[number],
                                    self.C_case[number], self.C_food[number], self.C_air[number], self.dt, 
									self.elementOnB[number], self.elementOn[number], self.lockonB[number], self.lockoffB[number], self.lockon[number], self.lockoff[number], self.cycle_off_base[number], 
                                    self.cycle_on_base[number], self.cycle_off_grid[number], self.cycle_on_grid[number]) for number in range(self.numRF)]

    # Baseline simulations
    # Todo: Only need run baseline in the first call of the grid service
    # It will generate and save a baseline for one day simulation with correct time resolution
    
    # def process_request(self, ServiceRequest):
        
    #     response = self.ExecuteFleet(ServiceRequest)   #response        
    #     return response     
    
    def get_time_of_the_day(self, ts):
        """ Method to calculate the time of the day in seconds to for the simulation of the feets """
        h, m, s = ts.hour, ts.minute, ts.second
        # Convert the hours, minutes, and seconds to seconds: referenced to 0 AM
        t = int(h) * 3600 + int(m) * 60 + int(s)
        if t >= 0:
            return t
        else:
            return t + 24*3600

    def process_request(self, fleet_request):
        """
        This function takes the fleet request and repackages it for the integral run function
        :param fleet_request: an instance of FleetRequest
        :return fleet_response: an instance of FleetResponse
        ## Follow the example of EV
        """
        ts = fleet_request.ts_req   # starting time
        dt = int(fleet_request.sim_step.total_seconds())   #fleet_request.sim_step  # Sim_step is how long a simulation time step
        # dt in timedelta format
        p_req = fleet_request.P_req
        q_req = fleet_request.Q_req

        # call run function with proper inputs
        resp = self.run(p_req, q_req, self.SOC, self.time, dt, ts)

        return resp

    # Example code for Frequency Watt Function

    def frequency_watt(self, p_req = 0, p_prev = 0, ts=datetime.utcnow(), location=0, db_UF = 0.05, db_OF = 0.05):
        """
        This function takes the requested power, date, time, and location
        and modifys the requested power according to the configured FW21 
        :param p_req: real power requested, ts:datetime opject,
               location: numerical designation for the location of the BESS
        :return p_mod: modifyed real power based on FW21 function
        """
        f = self.grid.get_frequency(ts,location)
        
        if (f < 60 - db_UF).any():
            p_mod = 0
        elif (f > 60 + db_OF).any():
            p_mod = p_req
        else:
            p_mod = p_prev
        
        return p_mod

    def update_soc_due_to_frequency_droop(self, initSOC, p_fleet, dt):
        """
        This method returns the modified state of charge of each subfleet 
        due to frequency droop in the grid
        """      
     
        charge_rate = p_fleet/(self.numRF*5.5)*0.1  # Heuristic soc change rate
        SOC_update = np.mean(initSOC) + charge_rate
        
        if SOC_update > 1:
            p_fleet = 0
            SOC_update = initSOC

        return p_fleet, SOC_update
    
    # Example code for VVO
    '''
     However, reactive power is not modeled in current model.
     So, we skipped the VVO function.
    '''

    def run(self, P_req, Q_req, initSOC, t, dt, ts): 
        #ExecuteFleet(self, Steps, Timestep, P_request, Q_request, forecast):
        # run(self, P_req=[0], Q_req=[0], ts=datetime.utcnow(), del_t=timedelta(hours=1)):    
        
        # Give the code the capability to respond to None requests
        if P_req == None:
            P_req = 0
        if Q_req == None:
            Q_req = 0      
          
        # run through fleet once as a forecast just to get initial conditions
        
        number = 0 # run through all the devices
        servsum = 0
        servmax = 0
        servmax2 = 0
        NumDevicesToCall = 0

        p_togrid = 0
        p_service = 0
        p_base = 0
        service_max = 0
        service_min = 0

        # laststep = step - 1

    #  decision making about which RF to call on for service, check if available at last step, if so then 
    #  check for SoC > self.minSOC and Soc < self.maxSOC

        P_request_perRF =  P_req/max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

        for n in range(self.numRF):
            if P_request_perRF < 0 and self.IsAvailableAdd[n] > 0:
                NumDevicesToCall += 1
            elif P_request_perRF > 0 and self.IsAvailableShed[n] > 0:
                NumDevicesToCall += 1          
    
        P_request_perRF =  P_req/max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

        #################################      
        for rfdg in self.RFs: #loop through all RFs
            TsetLast = self.TsetInitial[number]

            TairLastB = self.TairInitialB[number]    
            TfoodLastB = self.TfoodInitialB[number]
            TcaseLastB = self.TcaseInitialB[number]
			
            TairLast = self.TairInitial[number]    
            TfoodLast = self.TfoodInitial[number]
            TcaseLast = self.TcaseInitial[number]


            if P_req<0 and self.IsAvailableAdd[number] > 0 :
            # For step >=1, can use last step temperature...        
                response = rfdg.FRIDGE(TairLastB, TfoodLastB, TcaseLastB, TairLast, TfoodLast, TcaseLast, TsetLast, self.Tamb[number][self.step], self.R_case[number], self.R_food[number], self.R_infil[number],
                                        self.C_case[number], self.C_food[number], self.C_air[number], P_request_perRF, dt,  
                                        self.elementOnB[number], self.elementOn[number], self.lockonB[number], self.lockoffB[number], self.lockon[number], self.lockoff[number], 
                                        self.cycle_off_base[number], self.cycle_on_base[number], self.cycle_off_grid[number], self.cycle_on_grid[number])
                P_req =  P_req - response.Eservice

                if P_req >= 0:   # all the service request has been met
                    P_req = 0

            elif P_req>0 and self.IsAvailableShed[number] > 0 :
            # For step >=1, can use last step temperature...                                
                response = rfdg.FRIDGE(TairLastB, TfoodLastB, TcaseLastB, TairLast, TfoodLast, TcaseLast, TsetLast, self.Tamb[number][self.step], self.R_case[number], self.R_food[number], self.R_infil[number],
                                        self.C_case[number], self.C_food[number], self.C_air[number], P_request_perRF, dt,  
                                        self.elementOnB[number], self.elementOn[number], self.lockonB[number], self.lockoffB[number], self.lockon[number], self.lockoff[number], 
                                        self.cycle_off_base[number], self.cycle_on_base[number], self.cycle_off_grid[number], self.cycle_on_grid[number])
                P_req =  P_req - response.Eservice    

                if P_req <= 0:      # all the service request has been met
                    P_req = 0
            # break

            else:        
                response = rfdg.FRIDGE(TairLastB, TfoodLastB, TcaseLastB, TairLast, TfoodLast, TcaseLast, TsetLast, self.Tamb[number][self.step], self.R_case[number], self.R_food[number], self.R_infil[number],
                                        self.C_case[number], self.C_food[number], self.C_air[number], 0, dt,  
                                        self.elementOnB[number], self.elementOn[number], self.lockonB[number], self.lockoffB[number], self.lockon[number], self.lockoff[number], 
                                        self.cycle_off_base[number], self.cycle_on_base[number], self.cycle_off_grid[number], self.cycle_on_grid[number])

            # assign returned parameters to associated lists to be recorded
            self.TsetInitial[number] = response.Tset
			
            self.TairInitialB[number] = response.TairB
            self.TfoodInitialB[number] = response.TfoodB
            self.TcaseInitialB[number] = response.TcaseB 
			
            self.elementOnB[number] = response.ElementOnB

            self.TairInitial[number] = response.Tair
            self.TfoodInitial[number] = response.Tfood
            self.TcaseInitial[number] = response.Tcase            

            self.elementOn[number] = response.ElementOn
            self.lockonB[number] = response.lockonB
            self.lockoffB[number]  = response.lockoffB
            self.lockon[number] = response.lockon
            self.lockoff[number]  = response.lockoff
            self.cycle_off_base[number] = response.cycle_off_base
            self.cycle_on_base[number] = response.cycle_on_base
            self.cycle_off_grid[number] = response.cycle_off_grid
            self.cycle_on_grid[number] = response.cycle_on_grid

            self.SOC[number] = response.SOC
            self.SOCb[number] = response.SOC_b
            self.IsAvailableAdd[number] = response.IsAvailableAdd
            self.IsAvailableShed[number] = response.IsAvailableShed

            self.AvailableCapacityAdd[number] = response.AvailableCapacityAdd 
            self.AvailableCapacityShed[number] = response.AvailableCapacityShed 
            self.ServiceCallsAccepted[number] = response.ServiceCallsAccepted

            self.ServiceProvided[number] = response.Eservice

            p_togrid += response.Eused

            # resp.P_togrid_max += response.PusedMax
            # resp.P_togrid_min += response.PusedMin 

            p_service += response.Eservice   #Eused/10  #Eservice    

            p_base += response.Pbase

            # FleetResponse.sim_step = response.sim_step       
            number += 1  # go to next device

            if P_req>=0:
                service_max += response.AvailableCapacityShed # NOTE THIS ASSUMES THE MAX SERVICE IS LOAD SHED
            else:
                service_min += response.AvailableCapacityAdd  # NOTE THIS ASSUMES THE MIN SERVICE IS LOAD ADD
            
        self.step += 1
		
		# Output Fleet Response

        resp = FleetResponse()

        # Positive Prequest means reducing power consumption

        resp.ts = ts
        resp.sim_step  = timedelta(seconds=dt)

        resp.P_service = []
        resp.P_service_max = []  # positive only?
        resp.P_service_min = []
        resp.P_togrid = []
        resp.P_togrid_max = []
        resp.P_togrid_min = []
        resp.P_forecast = []
        resp.P_base = []
        resp.E = []
        resp.C = []        
            
        # resp.P_dot_up = resp.P_togrid_max / ServiceRequest.Timestep.seconds

        resp.P_service = p_service
        resp.P_service_max = service_max  # positive decrease loads
        resp.P_service_min = service_min  # negative increase loasd

        resp.P_base = -p_base
        resp.P_togrid = -p_togrid 
        resp.P_togrid_max = -(p_base-service_max) 
        resp.P_togrid_min = -(p_base-service_min)       

        resp.E = 0
        resp.C = 0 # response.SOC/(self.numRF)

        resp.Q_togrid = 'NA'
        resp.Q_service = 'NA'
        resp.Q_service_max = 'NA'
        resp.Q_service_min = 'NA'
        resp.Q_togrid_min = 'NA'  
        resp.Q_togrid_max = 'NA'

        resp.Q_dot_up = 'NA'
        resp.Q_dot_down = 'NA'
        resp.P_dot_up = 0
        resp.P_dot_down = 0

        resp.dT_hold_limit  = 'NA'
        resp.T_restore      = 'NA'
        resp.Strike_price   = 'NA'
        resp.SOC_cost       = 'NA'

        # TotalServiceProvidedPerTimeStep[step] = -1.0*self.P_service   # per time step for all hvacs  -1.0*        
        """
        Modify the power and SOC of the different subfeets according 
        to the frequency droop regulation according to IEEE standard
        """    
        if self.FW21_Enabled and self.is_autonomous:
            power_ac = resp.P_service_max
            p_prev = resp.P_togrid
            power_fleet = self.frequency_watt(power_ac, p_prev, self.ts, self.location, self.db_UF_subfleet, self.db_OF_subfleet)
            power_fleet_step, SOC_step = self.update_soc_due_to_frequency_droop(initSOC, power_fleet, dt)

        self.time = t + dt
        self.ts = self.ts + timedelta(seconds = dt)
        # Restart time if it surpasses 24 hours
        if self.time > 24*3600:
            self.time = self.time - 24*3600

        # Impact Metrics
        # Update the metrics
        Ttotal = 0
        SOCTotal = 0

        self.cycle_basee = np.sum(self.cycle_off_base)
        self.cycle_basee += np.sum(self.cycle_on_base)
        self.cycle_grid = np.sum(self.cycle_off_grid)
        self.cycle_grid += np.sum(self.cycle_on_grid)

        for numberr in range(self.numRF-1):    
            if self.TairInitial[numberr]>=self.TsetInitial[numberr] + 3:  #assume 2F, self.deadband
                self.unmet_hours += 1*self.sim_step/3600.0

        self.ave_TairB = np.average(self.TairInitialB)
        self.ave_Tair = np.average(self.TairInitial)
        self.SOCb_metric = np.average(self.SOCb)
        self.SOC_metric = np.average(self.SOC)
        self.unmet_hours = self.unmet_hours/self.numRF

        self.ratio_P_togrid_P_base = resp.P_togrid/(resp.P_base)
        self.energy_impacts += abs(resp.P_service)*(self.sim_step/3600)

        return resp 
     
    #################################################   
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
        SOC = self.SOC 

        for number in range(self.numRF): #loop through all RFs
            TairR = self.TairInitial[number]
            TfoodR = self.TfoodInitial[number]
            TcaseR = self.TcaseInitial[number]
           
            SOCR = self.SOC[number]

            elementOnR = self.elementOn[number]
            lockonR = self.lockon[number]
            lockoffR = self.lockoff[number]
            cycle_offR = self.cycle_off_base[number]
            cycle_on_baseR = self.cycle_on_base[number]
            cycle_off_gridR = self.cycle_off_grid[number]
            cycle_on_gridR = self.cycle_on_grid[number]

        # Iterate and process each request in fleet_requests
        for req in requests:
            ts = req.ts_req
            dt = int(req.sim_step.total_seconds())
            p_req = req.P_req
            q_req = req.Q_req
            res = self.run(p_req, q_req, self.SOC, self.time, dt, ts)

            responses.append(res)
                    
        # reset the model
        for number in range(self.numRF): #loop through all RFs
            self.soc = SOCR 
            self.TairInitial[number] = TairR
            self.TfoodInitial[number] = TfoodR
            self.TcaseInitial[number] = TcaseR
            

            self.elementOn[number] = elementOnR
            self.lockon[number] = lockonR
            self.lockoff[number] = lockoffR
            self.cycle_off_base[number] = cycle_offR
            self.cycle_on_base[number] = cycle_on_baseR
            self.cycle_off_grid[number] = cycle_off_gridR
            self.cycle_on_grid[number] = cycle_on_gridR
  
        return responses
 

    def run_baseline_simulation(self):
        """ 
        Method to run baseline simulation and store power level and SOC of 
        the sub fleets.
        """
        n_days_base = 1  # Only consider 1 day simulation, self.n_days_base
        sim_time = 24*3600 # one day in seconds
        
        print("Running day-ahead baseline simulation ...")       
        print("Running baseline right away charging strategy ...")
        baseline_soc, baseline_std_soc, baseline_power, baseline_cycles, baseline_Tin, baseline_std_Tin, baseline_Tin_max, baseline_Tin_min = self.run_baseline_right_away(n_days_base, sim_time)
                       
        print("Exported baseline soc, Temperatures, power and RF cycles ...")
        
        base_path = dirname(abspath(__file__))
        path = join(base_path,'data')
        
        # Already saved inside the right away function
        # baseline_soc.to_csv(join(path, r'SOC_baseline.csv'), index = False)
        # baseline_power.to_csv(join(path, r'power_baseline.csv'), index = False)
        # baseline_Tin.to_csv(join(path, r'Tin_baseline.csv'), index = False)
        # baseline_Tin_max.to_csv(join(path, r'Tin_max_baseline.csv'), index = False)
        # baseline_Tin_min.to_csv(join(path, r'Tin_min_baseline.csv'), index = False)
        print("Exported")

    def run_baseline_right_away(self, n_days_base, sim_time):
        """ Method to run baseline with 1-day ahead simulation strategy """
        baseline_power = np.zeros([sim_time, ])
        baseline_cycles = np.zeros([sim_time, ])
        baseline_Tin = np.zeros([sim_time, ])
        baseline_std_Tin = np.zeros([sim_time, ])
        baseline_Tin_max = np.zeros([sim_time, ])
        baseline_Tin_min = np.zeros([sim_time, ])
        baseline_soc = np.zeros([sim_time, ])   
        baseline_std_soc = np.zeros([sim_time, ]) 

        EIRrated = 0.31019
        Qrated=14600

        # inputs and outputs path
        inputs_file='./fleets/Refridge_fleet/data_file/LasVegas_HighCDD.csv'
        bldg_file='./fleets/Refridge_fleet/data_file/normal_building_para.xlsx'
        save_dir='./fleets/Refridge_fleet/data_file/baseline'


        #read in weather data and increase resolution to match time step of simulation
        inputs=pd.read_csv(inputs_file, sep=',',skipfooter=48,engine='python')
        inputs[c.COL_DATETIME]=pd.to_datetime(inputs[c.COL_DATETIME])
        inputs=inputs.set_index(c.COL_DATETIME)
        inputs_ts=inputs.resample(str(self.sim_step)+'T').interpolate()
       
        for day in range(n_days_base):
            print("Day %i" %(day+1))
            
            #initialize dataframes
            timeB = np.array(np.arange(0,60*60*24,self.sim_step))
            plot_timeB = np.array(np.arange(0,24,self.sim_step/3600))

            Tin=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            Tmass=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            Twall=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            Tattic=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            ACstatus=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            dTin=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            dTmass=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            dTwall=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            dTattic=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            Power=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            cycles=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            SOC=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numRF))
            
            num_homes = self.numRF            
            
            #Load building characteristics from file
            df_bldg=pd.DataFrame.from_csv(bldg_file,sep=',')
            
            #Initialize Temperatures and assign building and AC characteristics
            b=[0]*num_homes
            ac=[0]*num_homes
            for i in range(0,num_homes):
                b[i]=building(df_bldg.T_in[i],df_bldg.T_mass[i],df_bldg.T_wall[i],df_bldg.T_attic[i],df_bldg.Rwall[i],df_bldg.Rattic[i],df_bldg.Rwin[i],df_bldg.SHGC[i],df_bldg.Cwall[i],df_bldg.Cin[i],df_bldg.C1[i],df_bldg.C2[i],df_bldg.C3[i],df_bldg.Cattic[i],df_bldg.Rroof[i],df_bldg.Cmass[i],df_bldg.Rmass[i],df_bldg.Sp1[i],df_bldg.Sp2[i],df_bldg.Sp3[i],df_bldg.Qrated[i],df_bldg.EIRrated[i],df_bldg.TinWB[i],df_bldg.Initial_On[i])
                Tin.iloc[0,i]=b[i].T_in
                Tmass.iloc[0,i]=b[i].T_mass
                Twall.iloc[0,i]=b[i].T_wall
                Tattic.iloc[0,i]=b[i].T_attic

                ac[i]=AC(df_bldg.Qrated[i],df_bldg.EIRrated[i])
            
            #Main simulation loop    
            for i in range(0,int(1440*60/self.sim_step)):
                for j in range(0,num_homes):                    
                    
                    if i>0:   #initialize AC status for each timestep to prior state
                        ACstatus.iloc[i,j]=ACstatus.iloc[i-1,j]
                    else:     #Set AC status based on file input for first timestep
                        ACstatus.iloc[i,j]=b[j].Initial_On
                    if Tin.iloc[i,j]>=self.Tset+self.deadband and ACstatus.iloc[max(i-self.shortcycle_ts,0):i,j].sum()==0:  #if temp is above deadband and unit has not run in past duration corresponding to short cycle timer turn on unit
                        ACstatus.iloc[i,j]=1.0
                    if Tin.iloc[i,j]<=self.Tset-self.deadband:    #if temperature is below bottom deadband, turn off unit
                        ACstatus.iloc[i,j]=0.0
                    #count cycles
                    if i>0 and ACstatus.iloc[i-1,j]==1.0 and ACstatus.iloc[i,j]==0.0:
                        cycles.iloc[i,j]=1.0
                        
                    #calculate power use for each AC based on status
                    Power.iloc[i,j]=ACstatus.iloc[i,j]*Capacity(ac[j],inputs_ts[c.COL_TOUT][i],b[j].TinWB)*EIR(ac[j],inputs_ts[c.COL_TOUT][i],b[j].TinWB)
                    
                    # calculate SOC for each AC
                    SOC.iloc[i,j] = (self.Tset+self.deadband - Tin.iloc[i,j])/(2*deadband)

                    #building model dT calculations
                    dTin.iloc[i,j]=ts*1.0/b[j].Cin*((Twall.iloc[i,j]-Tin.iloc[i,j])*2.0/b[j].Rwall
                            +(Tattic.iloc[i,j]-Tin.iloc[i,j])/b[j].Rattic
                            +(Tmass.iloc[i,j]-Tin.iloc[i,j])/b[j].Rmass+inputs_ts[c.COL_QIHL][i]*b[j].C1*b[j].Sp1
                            +inputs_ts[c.COL_RADWIN][i]*b[j].SHGC*25.76*b[j].C3*b[j].Sp3
                            -ACstatus.iloc[i,j]*Capacity(ac[j],inputs_ts[c.COL_TOUT][i],b[j].TinWB)*SHR(inputs_ts[c.COL_TOUT][i],Tin.iloc[i,j],b[j].TinWB)*b[j].C2*b[j].Sp2
                            +(inputs_ts[c.COL_TOUT][i]-Tin.iloc[i,j])/b[j].Rwin)
                    dTmass.iloc[i,j]=ts*1.0/b[j].Cmass*((Tin.iloc[i,j]-Tmass.iloc[i,j])/b[j].Rmass
                            +inputs_ts[c.COL_QIHL][i]*b[j].C1*(1-b[j].Sp1)
                            +inputs_ts[c.COL_RADWIN][i]*b[j].SHGC*25.76*b[j].C3*(1-b[j].Sp3)
                            -ACstatus.iloc[i,j]*Capacity(ac[j],inputs_ts[c.COL_TOUT][i],b[j].TinWB)*SHR(inputs_ts[c.COL_TOUT][i],Tin.iloc[i,j],b[j].TinWB)*b[j].C2*(1-b[j].Sp2))
                    dTwall.iloc[i,j]=ts*1.0/b[j].Cwall*((inputs_ts['Tsolw'].iloc[i]-Twall.iloc[i,j])*2.0/b[j].Rwall
                            +(Tin.iloc[i,j]-Twall.iloc[i,j])*2.0/b[j].Rwall)
                    dTattic.iloc[i,j]=ts*1.0/b[j].Cattic*((inputs_ts['Tsolr'].iloc[i]-Tattic.iloc[i,j])/b[j].Rroof
                                +(Tin.iloc[i,j]-Tattic.iloc[i,j])/b[j].Rattic)
                    
                    #calculate temperatures for next time step
                    if i<(1440*60/ts-1):
                        Tin.iloc[i+1,j]=Tin.iloc[i,j]+dTin.iloc[i,j]
                        Tmass.iloc[i+1,j]=Tmass.iloc[i,j]+dTmass.iloc[i,j]
                        Tattic.iloc[i+1,j]=Tattic.iloc[i,j]+dTattic.iloc[i,j]
                        Twall.iloc[i+1,j]=Twall.iloc[i,j]+dTwall.iloc[i,j]

            # calculate peak power and plot data
            PeakPower=Power.sum(axis=1).max()*1.0 # plot out the peak power in kW
            Plot_Power=np.full(len(plot_time),PeakPower/1000.0)
            fig,ax = plt.subplots(2,1,figsize=(6,8),sharey='row')
            p1=ax[0].plot(plot_time,Power.sum(axis=1)/1000.0,color='blue',linestyle='solid',label='Baseline')
            ax[0].plot(plot_time,Plot_Power,color='black',linestyle='--',label='Targeted Power')
            ax[0].set_ylabel('Total Power (kW)')
            ax[1].set_ylabel('Indoor Temperature ($^\circ$C)')
            ax[1].set_xlabel('Hour of Day')
            p2=ax[1].plot(plot_time,Tin.mean(axis=1),color='blue',linestyle='solid',label='Baseline Avg')
            p3=ax[1].plot(plot_time,Tin.max(axis=1),color='blue',linestyle='dotted',label='Baseline Min/Max')
            p4=ax[1].plot(plot_time,Tin.min(axis=1),color='blue',linestyle='dotted',label='_nolegend_')
            
            # Saves baseline data to csv
            #ToDo: needs cut the whole day simulation to compare only segment with providing grid services
            # But, that requires the simulation steps information.

            Power.to_csv(str(save_dir)+'\\Power_base'+'.csv')
            Tin.to_csv(str(save_dir)+'\\Tin_base'+'.csv')
            SOC.to_csv(str(save_dir)+'\\SOC_base'+'.csv')
            cycles.to_csv(str(save_dir)+'\\Cycles_base'+'.csv')
            
            # return values
            baseline_power = Power.sum(axis = 1)
            baseline_cycles = cycles.sum(axis = 1)

            baseline_soc = SOC.mean(axis = 1)
            baseline_std_soc = SOC.std(axis = 1)

            baseline_Tin = Tin.mean(axis = 1)
            baseline_std_Tin = Tin.std(axis = 1)
            baseline_Tin_max = Tin.max(axis=1)
            baseline_Tin_min = Tin.min(axis=1)

            baseline_soc = SOC.mean(axis = 1)
            baseline_std_soc = SOC.std(axis = 1)
                    
        return baseline_soc, baseline_std_soc, baseline_power, baseline_cycles, baseline_Tin, baseline_std_Tin, baseline_Tin_max, baseline_Tin_min
    
    
    def output_impact_metrics(self, service_name):   
        impact_metrics_DATA = [["Impact Metrics File"],
                                ["ave_Tair_base", "ave_Tair", "Cycle_base", "Cycle_service", "SOC_base", "SOC_service", "Unmet Hours"]]
        
        impact_metrics_DATA.append([str(self.ave_TairB), str(self.ave_Tair), str(self.cycle_basee), str(self.cycle_grid), str(self.SOCb_metric), str(self.SOC_metric), str(self.unmet_hours)])
        impact_metrics_DATA.append(["P_togrid/P_base ratio:", self.ratio_P_togrid_P_base])
        impact_metrics_DATA.append(["Energy Impacts (kWh):", self.energy_impacts])

        metrics_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'integration_test', service_name)
        ensure_ddir(metrics_dir)
        metrics_filename = 'ImpactMetrics_' + service_name + '_Fridge' + '_' + datetime.now().strftime('%Y%m%dT%H%M')  + '.csv'
        with open(join(metrics_dir, metrics_filename), 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(impact_metrics_DATA)   

    #     pass

    def change_config(self, fleet_config):
        """
        This function updates the fleet configuration settings programatically.
        :param fleet_config: an instance of FleetConfig
        """

        # change config
        self.is_P_priority = fleet_config.is_P_priority
        self.is_autonomous = fleet_config.is_autonomous
        self.FW_Param = fleet_config.FW_Param # FW_Param=[db_UF,db_OF,k_UF,k_OF]
        self.fw_function.db_UF = self.FW_Param[0]
        self.fw_function.db_OF = self.FW_Param[1]
        self.fw_function.k_UF = self.FW_Param[2]
        self.fw_function.k_OF = self.FW_Param[3]
        self.autonomous_threshold = fleet_config.autonomous_threshold
        self.Vset = fleet_config.v_thresholds

    def assigned_service_kW(self):
        """ 
        This function allows weight to be passed to the service model. 
        Scale the service to the size of the fleet
        """
        return self.service_weight*self.fleet_rating
    
    def print_performance_info(self):
        """
        This function is to dump the performance metrics either to screen or file or both
        :return:
        """
        pass
    ###############################################################################    
    '''
    Add necessary weather data by randomly sampling from a weather database for a summer cooling month;
    since we only stored one month data in 10 min resolution here, this code will automatically interpolate
    the data to desired resolution by ignoring the actual month in the 'time' format.
    '''
    #### Interpolate the time resolution of the disturbances

    ##### Randomly pick the Tamb and IHL
def get_daily_conditions(climate_location,  timestep_s, start_time):
            #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        loc = dict()
        loc["Miami"] = 0
        loc["Phoenix"] = 1
        loc["Atlanta"] = 2
        loc["Las Vegas"] = 3
        loc["Denver"] = 4
        loc["Minneapolis"] = 5

        num_steps = 10*3600*24.0/timestep_s   

        try:
            amb_temp_column = loc[climate_location]
            IHG_column = loc[climate_location]
        except IndexError:
            raise IndexError("Error! Only allowed installation locations for now !!!")

        dt = datetime.strptime(str(start_time), '%Y-%m-%d %H:%M:%S') #.%f
        start_time_dec = dt.hour + dt.minute/60.0 + dt.second/3600.0

        new_time_list = np.linspace(start_time_dec, start_time_dec+timestep_s*num_steps/3600.0, num_steps)

        Tamb = []
        IHG = []

        # Tout and IHG profiles preprocessed for 10 mins,
        # if other time step, better to do preprocess outside the main function here
        # or use timestep_min below (we set timestep_min = 10 by default)
        ambient_cond_file = pd.read_excel(r'./fleets/Refridge_fleet/data_file/Cities_Tout_July_10mins.xlsx') #load steply ambient air temperature file
        ambient_cond_file = np.matrix(ambient_cond_file)
        Tamb = ambient_cond_file[:,amb_temp_column]
        Tamb = np.squeeze(np.asarray(Tamb))

        # turn from 10 min original time resoution to any time resolution in seconds
        Tamb_num_steps = Tamb.shape[0]
        Tamb_stepsize_min = 10
        Tamb_orig_time = np.linspace(start_time_dec,
                                        start_time_dec + Tamb_stepsize_min*Tamb_num_steps/60.0,
                                        Tamb_num_steps)       
        new_Tamb = np.interp(new_time_list, Tamb_orig_time, Tamb)

        
        return new_Tamb









