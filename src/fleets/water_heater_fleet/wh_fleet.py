# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling a fleet of water heaters
@author: Chuck Booten (NREL), Jeff Maguire (NREL)
"""

# code needed for GLOBAL fleet_interface
import sys
from os.path import dirname, abspath, join
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))
################################################################

from configparser import ConfigParser
# import datetime
# from datetime import timedelta

from datetime import datetime, timedelta

from fleet_interface import FleetInterface
from fleet_response import FleetResponse
#from fleets.water_heater_fleet.load_config import LoadConfig
from load_config import LoadConfig
from frequency_droop import FrequencyDroop

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import random
import pandas as pd
import scipy as sp
import time
import csv
import os

from wh import WaterHeater

class WaterHeaterFleet(FleetInterface):   #FleetInterface
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
        self.base_path = dirname(abspath(__file__))
        
        # Read config file
        config = ConfigParser()
        config.read(join(self.base_path, 'config.ini'))
       
        # Load config file and store data in a dataframe
        LC = LoadConfig(config)
        self.df_WHModels = LC.get_config_models()
        
        # Run baseline power to store baseline power and SOC if parameters 
        # of the fleet are changed. ONLY ASSIGN TRUE IF YOU CHANGE THE 
        # PARAMETERS OF THE FLEET AS IT WILL DRAMATICALLY INCREASE THE CPU TIME
        self.run_baseline = LC.get_run_baseline()
        # Establish the properties of the grid on which the fleet is connected on
        self.grid = GridInfo
        # Get cur directory
        self.base_path = dirname(abspath(__file__))
        
        #Input data for water heaters (probably should be moved to config.ini)
        self.numWH = 10 #number of water heaters to be simulated to represent the entire fleet
        self.Fleet_size_represented = max(self.numWH, 1e5)#size of the fleet that is represented by self.numWH
#        addshedTimestep NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 0.1, 0.2, 0.5, 1,2,3,4,5,6,10,12,15,20,30, 60, etc.
        #self.MaxNumAnnualConditions = 20 #max # of annual conditions to calculate, if more WHs than this just reuse some of the conditions and water draw profiles

        " TODO: update this sim_step in main interface "

        self.sim_step = s_step.total_seconds() #1 * 10 # in seconds
        # self.sim_step = 10 #1 * 10 # in seconds

               
        # #%% Frequency-watt parameters
        # FrequencyWatt='Frequency Watt'
        # self.db_UF=float(LC.get(FW,'db_UF'))
        # self.db_OF=float(LC.get(FW,'db_OF'))
        # self.k_UF=float(self.config.get(FrequencyWatt,'k_UF'))
        # self.k_OF=float(self.config.get(FrequencyWatt,'k_OF'))


        # How to calculate effective fleet rating: this is going to be poorly
        # met because it does not consider random availability of the fleet. 
        # However this seems to be the best approximation
        self.fleet_rating = (self.numWH * 4.5)  # unit power is 4.5 kw

        # Weight used to scale the service request
        self.service_weight = LC.get_service_weight()    
        
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
            self.db_UF_subfleet = np.random.uniform(low = self.db_UF[0], high = self.db_UF[1], size = (self.numWH, ))
            self.db_OF_subfleet = np.random.uniform(low = self.db_OF[0], high = self.db_OF[1], size = (self.numWH, ))
        
        # Impact metrics of the fleet
        metrics = LC.get_impact_metrics_params()
        
        # Aveage tank baseline
        self.ave_Tin = metrics[0]
        # Aveage tank temperature under grid service
        self.ave_Tin = metrics[1]
        # Cylces in baseline
        self.cycle_basee = metrics[2]
        # Cylces in grid operation
        self.cycle_grid = metrics[3]
        # State of Charge of the battery equivalent model under baseline
        self.SOCb_metric = metrics[4]
        # State of Charge of the battery equivalent model
        self.SOC_metric = metrics[5]
        # Unmet hours of the fleet
        self.unmet_hours = metrics[6]
        
               
        ########### initial tank temperatures and setpoint temperature
        # for capacity, type, location and max. number of service calls need to specify discrete values and randomly sample to get a desired distribution 
        self.MaxNumAnnualConditions = 20
        self.CapacityMasterList = [50,50,50,50,50,50,50,50,40,40,80] #70% 50 gal, 20% 40 gal, 10% 80 gal
        self.TypeMasterList = ['ER','ER','ER','ER','ER','ER','ER','ER','ER','HP'] #elec_resis 90% and HPWH 10%
        self.LocationMasterList =['living','living','living','living','unfinished basement'] #80% living, 20% unfinished basement for now
        self.MaxServiceCallMasterList = [100,80,80, 200, 150, 110, 50, 75, 100] # this is the max number of annual service calls for load add/shed.
        self.TtankInitialMean = 123 #deg F
        self.TtankInitialStddev = 9.7 #deg F
        self.TsetInitialMean = 123 #deg F
        self.TsetInitialStddev = 9.7 #deg F
        self.minSOC = 0.2 # minimum SoC for aggregator to call for shed service
        self.maxSOC = 0.8 # minimum SoC for aggregator to call for add service
        self.minCapacityAdd = 350 #W-hr, minimum add capacity to be eligible for add service
        self.minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
        
         ########################################################################
        
        # Initialize timestamps and local times of the class for future calculations
        self.initial_ts = ts # time stamp to start the simulation
        self.ts = ts
        self.initial_time = self.get_time_of_the_day(ts)
        self.time = self.get_time_of_the_day(ts)
        self.dt = 60       # time step (in seconds)

        ##################################     
        #    Initializing lists to be saved to track indivisual water heater performance over each timestep

        # Randomly set up and mix the water heater fleet
        # Random seed for regenerating the same result
        self.seed = 1
        np.random.seed(self.seed)

        # generate distribution of initial water heater fleet states.
        # random initial temperatures (with a distribution based on field research by Lutz)
        
        self.TtankInitial = np.random.normal(self.TtankInitialMean,self.TtankInitialStddev,self.numWH)
        self.TsetInitial = np.random.normal(self.TsetInitialMean,self.TsetInitialStddev,self.numWH)
        for x in range(self.numWH):
            self.TsetInitial[x] = max(self.TsetInitial[x],110)
            if self.TtankInitial[x] > self.TsetInitial[x]:
                self.TtankInitial[x] = self.TsetInitial[x]

        Capacity = [random.choice(self.CapacityMasterList) for n in range(self.numWH)]
#        Capacity_fleet_ave = sum(Capacity)/self.numWH
        self.Type = [random.choice(self.TypeMasterList) for n in range(self.numWH)]
        Location = [random.choice(self.LocationMasterList) for n in range(self.numWH)]
        self.MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numWH)]
        
        climate_location = 'Denver' # only allowable climate for now since the pre-run water draw profile generator has only been run for this climate
        #10 different profiles for each number of bedrooms, bedrooms can be 1-5, gives 50 different draw profiles, can shift profiles by 0-364 days,gives 365*50 = 18250 different water draw profiles for each climate
        self.Tamb = []
        self.RHamb = []
        self.Tmains = []
        self.hot_draw =[]
        self.mixed_draw = []
        self.draw = []
        for a in range(self.numWH):             
            if a <= (self.MaxNumAnnualConditions-1): #if self.numWH > MaxNumAnnualConditions just start reusing older conditions to save computational time
                numbeds = random.randint(1, 5) 
                shift = random.randint(0, 364)
                unit = random.randint(0, 9)
                (tamb, rhamb, tmains, hotdraw, mixeddraw) = get_annual_conditions(climate_location,  Location[a], shift, numbeds, unit, self.dt, self.ts)
    #            print('tamb',tamb)
        
                self.Tamb.append(tamb)#have a Tamb for each step for each water heater being simulated 
                self.RHamb.append(rhamb)
                self.Tmains.append(tmains)
                self.hot_draw.append(hotdraw)
                self.mixed_draw.append(mixeddraw)
                self.draw.append(hotdraw + 0.3 * mixeddraw)#0.3 is so you don't need to know the exact hot/cold mixture for mixed draws, just assume 70% hot is needed for mixed
    #            print('len Tamb',len(Tamb[0]))
    
            else: #start re-using conditions
                self.Tamb.append(self.Tamb[a % self.MaxNumAnnualConditions][:])
                self.RHamb.append(self.RHamb[a % self.MaxNumAnnualConditions][:])
                self.Tmains.append(self.Tmains[a % self.MaxNumAnnualConditions][:])
                self.hot_draw.append(self.hot_draw[a % self.MaxNumAnnualConditions][:])
                self.mixed_draw.append(self.mixed_draw[a % self.MaxNumAnnualConditions][:])
                self.draw.append(self.hot_draw[a-self.MaxNumAnnualConditions][:] + 0.3 *self. mixed_draw[a-self.MaxNumAnnualConditions][:])
        # print('len Tamb',len(Tamb[0]), len(Tamb))
        # print('len hotdraw',len(hot_draw[0]), len(hot_draw))
        # print('Tamb',Tamb)

        draw_fleet = sum(self.draw)# this sums all rows, where each row is a WH, so gives the fleet sum of hot draw at each step
        self.draw_fleet_ave = draw_fleet/self.numWH  # this averages all rows, where each row is a WH, so gives the fleet average of hot draw at each step
        
        
        self.MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numWH)]
        self.AvailableCapacityAdd = [0 for x in range(self.numWH)]
        self.AvailableCapacityShed = [0 for x in range(self.numWH)]
        self.ServiceCallsAccepted = [0 for x in range(self.numWH)]
        self.ServiceProvided = [0 for x in range(self.numWH)]

        self.IsAvailableAdd = np.random.randint(2, size=self.numWH+1)
        self.IsAvailableShed = np.random.randint(2, size=self.numWH+1)

        self.elementOnB = np.random.randint(2, size=self.numWH)
        self.elementOn = np.random.randint(2, size=self.numWH)

        self.cycle_off_base = [0 for x in range(self.numWH)]
        self.cycle_on_base = [0 for x in range(self.numWH)]
        self.cycle_off_grid = [0 for x in range(self.numWH)]
        self.cycle_on_grid = [0 for x in range(self.numWH)]

        # MaxServiceAddedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]
        # MaxServiceShedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]

        self.TotalServiceCallsAcceptedPerWH = [0 for y in range(self.numWH)]    
   
        self.SoCInit = [0.8 for y in range(self.numWH)]
        self.SOC = self.SoCInit
        self.SOCb = self.SoCInit

        self.AvailableCapacityAddInit = [0 for y in range(self.numWH)]
        self.AvailableCapacityShedInit = [0 for y in range(self.numWH)]

        self.IsAvailableAddInit = np.random.randint(2, size=self.numWH+1)
        self.IsAvailableShedInit = np.random.randint(2, size=self.numWH+1)
        
        self.step = 0

        ##############################################################################################################
 
        #    Initializing the WH models
       
        self.whs = [WaterHeater(self.Tamb[0], self.RHamb[0], self.Tmains[0], 0, 0, Capacity[number], self.Type[number], Location[number], 0, self.MaxServiceCalls[number]) for number in range(self.numWH)]
    
    def get_time_of_the_day(self, ts):
        """ Method to calculate the time of the day in seconds for the simulation of the fleets """
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
        :return fleet_response: an instance of resp
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

    def frequency_watt(self, p_req = 0, p_prev = 0, ts=datetime.utcnow(), location=0, db_UF = 0.05, db_OF = 0.05):  #datetime.
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
        charge_rate = p_fleet / (self.numWH * 4.5) * 0.1  # Heuristic soc change rate
        SOC_update = initSOC + [charge_rate]
        
        if max(SOC_update) > 1:
            p_fleet = 0
            SOC_update = initSOC

        return p_fleet, SOC_update
    
    # Example code for VVO
    '''
     Electric resistance water heaters consume no reactive power
     TODO: Update when HPWHs are added
    '''

    def run(self, P_req, Q_req, initSOC, t, dt, ts): 
        #ExecuteFleet(self, Steps, Timestep, P_request, Q_request, forecast):
        # run(self, P_req=[0], Q_req=[0], ts=datetime.utcnow(), del_t=timedelta(hours=1)):    
        
        # Give the code the capability to respond to None requests
        
        
        if P_req == None:
            P_req = 0
        if Q_req == None:
            Q_req = 0      
        
        P_togrid = 0
        P_service = 0
        P_base = 0
        P_service_max = 0

        P_request_perWH = P_req / self.numWH # this is only for the first step

        number = 0 # run through all the devices

        NumDevicesToCall = 0
        P_service_max0 = 0

    #  decision making about which water heater to call on for service, check if available at last step, if so then 
    #  check for SoC > self.minSOC and Soc < self.maxSOC

        for n in range(self.numWH):
            if P_request_perWH < 0 and self.IsAvailableAdd[n] > 0 and self.SOC[n] < self.maxSOC:
                NumDevicesToCall += 1
            elif P_request_perWH > 0 and self.IsAvailableShed[n] > 0 and self.SOC[n] > self.minSOC:
                NumDevicesToCall += 1          
    
        P_request_perWH =  P_req/max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

        #################################      
        for wh in self.whs: #loop through all water heaters
            #create a .csv outputfile with each water heater's metrics
            outputfilename = join(self.base_path,"WH_fleet_outputs.csv")
            self.outputfile = open(outputfilename,"w")
            self.outputfile.write("Timestep,")
            if P_req <= 0 and self.IsAvailableAdd[number] > 0:
                response = wh.execute(self.TtankInitial[number], self.TsetInitial[number], self.Tamb[number][0], self.RHamb[number][0], self.Tmains[number][0], self.draw[number][0], P_request_perWH, self.Type, self.dt, self.draw_fleet_ave[0])
                P_req =  P_req - response.Eservice

            elif P_req > 0 and self.IsAvailableShed[number] > 0:
                response = wh.execute(self.TtankInitial[number], self.TsetInitial[number], self.Tamb[number][0], self.RHamb[number][0], self.Tmains[number][0], self.draw[number][0], P_request_perWH, self.Type, self.dt, self.draw_fleet_ave[0])
                P_req =  P_req - response.Eservice
            else:        
                response = wh.execute(self.TtankInitial[number], self.TsetInitial[number], self.Tamb[number][0], self.RHamb[number][0], self.Tmains[number][0], self.draw[number][0], P_request_perWH, self.Type, self.dt, self.draw_fleet_ave[0])
            self.outputfile.write("Ttank_{},".format(n) +"Tset_{},".format(n) +"Eused_{},".format(n) +"PusedMax_{},".format(n) +"Eloss_{},".format(n) +"ElementOn_{},".format(n) +"Eservice_{},".format(n) +"SOC_{},".format(n) +"AvailableCapAdd_{},".format(n) +"AvailableCapShed_{},".format(n) +"CallsAccepted_{},".format(n) +"AvailableAdd_{},".format(n) +"AvailableShed_{},".format(n) + "Hot+MixedDrawVolume_{},".format(n) + "Edel_{},".format(n))
            self.outputfile.write("\n")
            # assign returned parameters to associated lists to be recorded
            self.TtankInitial[number] = response.Ttank
            
            self.SOC[number] = response.SOC
            self.SOCb[number] = response.SOC_b
            self.IsAvailableAdd[number] = response.IsAvailableAdd
            self.IsAvailableShed[number] = response.IsAvailableShed
            
            self.AvailableCapacityAdd[number] = response.AvailableCapacityAdd 
            self.AvailableCapacityShed[number] = response.AvailableCapacityShed 
            self.ServiceCallsAccepted[number] = response.ServiceCallsAccepted

            self.ServiceProvided[number] = response.Eservice
            
            P_togrid += response.Eused

            # resp.P_togrid_max += response.PusedMax
            # resp.P_togrid_min += response.PusedMin 

            P_service += response.Eservice    

            P_base += response.Pbase   

            # resp.sim_step = response.sim_step       
            number += 1  # go to next device            

            if P_req<=0:
                P_service_max += response.AvailableCapacityShed # NOTE THIS ASSUMES THE MAX SERVICE IS LOAD SHED
            else:
                P_service_max0 += response.AvailableCapacityAdd
                P_service_max = -1.0*P_service_max0

        self.step += 1 # To advance the step by step in the disturbance file

        # Output Fleet Response

        resp = FleetResponse()

        resp.P_service = []
        resp.P_service_max = []
        resp.P_service_min = []
        resp.P_togrid = []
        resp.P_togrid_max = []
        resp.P_togrid_min = []
        resp.P_forecast = []
        resp.P_base = []
        resp.E = []
        resp.C = []
        resp.ts = ts
        resp.sim_step = dt    
        # resp.P_dot_up = resp.P_togrid_max / ServiceRequest.Timestep.seconds

        resp.P_service_max = P_service_max
        resp.P_service = P_service
        resp.P_base = P_base
        resp.P_togrid = P_togrid

        # Available Energy stored at the end of the most recent timestep
        # resp.E += response.Estored
        resp.E = 0
        resp.C += response.SOC / (self.numWH)

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

        resp.P_dot = resp.P_togrid / dt
        resp.P_service_min  = 0

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
            power_fleet, SOC_step = self.update_soc_due_to_frequency_droop(initSOC, power_fleet, dt)

        self.time = t + dt
        self.ts = self.ts + timedelta(seconds = dt)
        # Restart time if it surpasses 24 hours
        if self.time > 24*3600:
            self.time = self.time - 24*3600

        # Impact Metrics
        # Update the metrics
        '''
        Ttotal = 0
        SOCTotal = 0
     
        self.cycle_basee = np.sum(self.cycle_off_base)
        self.cycle_basee += np.sum(self.cycle_on_base)
        self.cycle_grid = np.sum(self.cycle_off_grid)
        self.cycle_grid += np.sum(self.cycle_on_grid)
        '''
        for number in range(self.numWH-1):    
            if response.Ttank<=self.TsetInitial[number] - 10 :  #assume 10F deadband (consistent with wh.py)
                self.unmet_hours += 1*self.sim_step/3600.0

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

        for number in range(self.numWH): #loop through all HVACs
            TinRB = self.TinInitialB[number]
            TwallRB = self.TwallInitialB[number]
            TmassRB = self.TmassInitialB[number]
            TatticRB = self.TatticInitialB[number]
            elementOnRB = self.elementOnB[number]

            TinR = self.TinInitial[number]
            TwallR = self.TwallInitial[number]
            TmassR = self.TmassInitial[number]
            TatticR = self.TatticInitial[number]

            SOC_bR = self.SOCb[number]
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

            return res
                    
        # reset the model
        for number in range(self.numWH): #loop through all HVACs
            self.SOC = SOCR 
            self.SOCb = SOC_bR 

            self.TinInitialB[number] = TinRB
            self.TwallInitialB[number] = TwallRB
            self.TmassInitialB[number] = TmassRB
            self.TatticInitialB[number] = TatticRB

            self.TinInitial[number] = TinR
            self.TwallInitial[number] = TwallR
            self.TmassInitial[number] = TmassR
            self.TatticInitial[number] = TatticR

            self.elementOn[number] = elementOnR
            self.elementOnB[number] = elementOnRB

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
                       
        print("Exported baseline soc, Temperatures, power and HVAC cycles ...")
        
        path = join(self.base_path,'data')
        
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
        inputs_file='./fleets/HVAC_fleet/data_file/LasVegas_HighCDD.csv'
        bldg_file='./fleets/HVAC_fleet/data_file/normal_building_para.xlsx'
        save_dir='./fleets/HVAC_fleet/data_file/baseline'


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

            Tin=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            Tmass=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            Twall=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            Tattic=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            ACstatus=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            dTin=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            dTmass=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            dTwall=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            dTattic=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            Power=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            cycles=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            SOC=pd.DataFrame(data=0,index=timeB,columns=range(0,self.numWH))
            
            num_homes = self.numWH            
            
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
                    SOC.iloc[i,j] = (self.Tset+self.deadband - Tin.iloc[i,j])/(2*self.deadband)

                    #building model dT calculations
                    ts = self.sim_step
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
            Plot_Power=np.full(len(plot_timeB),PeakPower/1000.0)
            fig,ax = plt.subplots(2,1,figsize=(6,8),sharey='row')
            p1=ax[0].plot(plot_timeB,Power.sum(axis=1)/1000.0,color='blue',linestyle='solid',label='Baseline')
            ax[0].plot(plot_timeB,Plot_Power,color='black',linestyle='--',label='Targeted Power')
            ax[0].set_ylabel('Total Power (kW)')
            ax[1].set_ylabel('Indoor Temperature ($^\circ$C)')
            ax[1].set_xlabel('Hour of Day')
            p2=ax[1].plot(plot_timeB,Tin.mean(axis=1),color='blue',linestyle='solid',label='Baseline Avg')
            p3=ax[1].plot(plot_timeB,Tin.max(axis=1),color='blue',linestyle='dotted',label='Baseline Min/Max')
            p4=ax[1].plot(plot_timeB,Tin.min(axis=1),color='blue',linestyle='dotted',label='_nolegend_')
            
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
                    
        return baseline_soc, baseline_std_soc, baseline_power, baseline_cycles, baseline_Tin, baseline_std_Tin, baseline_Tin_max, baseline_Tin_min
    
    
    def output_impact_metrics(self):   
        impact_metrics_DATA = [["Impact Metrics File"],
                                ["ave_Tin_base", "ave_Tin", "Cycle_base", "Cycle_service", "SOC_base", "SOC_service", "Unmet Hours"]]
        
        impact_metrics_DATA.append([str(self.ave_TinB), str(self.ave_Tin), str(self.cycle_basee), str(self.cycle_grid), str(self.SOCb_metric), str(self.SOC_metric), str(self.unmet_hours)])

        with open('impact_metrics.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(impact_metrics_DATA)     

    #     pass

    def change_config(self, fleet_config):
    #     """
    #     This function updates the fleet configuration settings programatically.
    #     :param fleet_config: an instance of FleetConfig
    #     """

        # change config
        self.is_P_priority = fleet_config.is_P_priority
        self.is_autonomous = fleet_config.is_autonomous
        self.FW_Param = fleet_config.FW_Param # FW_Param=[db_UF,db_OF,k_UF,k_OF]
        self.fw_function.db_UF = self.FW_Param[0]
        self.fw_function.db_OF = self.FW_Param[1]
        self.fw_function.k_UF = self.FW_Param[2]
        self.fw_function.k_OF = self.FW_Param[3]
        self.autonomous_threshold = fleet_config.autonomous_threshold
    #     self.Vset = fleet_config.v_thresholds

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


def get_annual_conditions(climate_location, installation_location, days_shift, n_br,unit, timestep_sec, start_time):

    #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
    timestep_min = timestep_sec / 60.
    #Decompose utc timestamp to get the starting hour
    startmonthindex = [[1,0],[2,31],[3,59],[4,90],[5,120],[6,151],[7,181],[8,212],[9,243],[10,273],[11,304],[12,334]]
    start_month = start_time.month
    start_day = start_time.day
    start_hour = start_time.hour
    for m in startmonthindex:
        if start_month == m[0]:
            start_day += m[1]
            break
    start_hr = (start_day-1) * 24. + start_hour
    
    num_steps_per_hr = int(np.ceil((60./float(timestep_min))))# how many hourly steps do you need to take if timestep is in minutes
    num_steps = 1 * 24 * 60 #TODO: what if someone wants to simulate longer than a month, or the simulation wraps over the end of the year?
    num_hrs = int(np.ceil(float(num_steps) / float(num_steps_per_hr)))
    num_mins = int(np.ceil(float(num_steps) * float(timestep_min )))
#        print('num_mins',num_mins)
    steps_per_min = int(np.ceil(1./float(timestep_min)))
    Tamb = []
    RHamb = []
    Tmains = []
    if climate_location != 'Denver':
        raise NameError("Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
    if installation_location == 'living':
        amb_temp_column = 1
        amb_rh_column = 2
    elif installation_location == 'unfinished basement':
        amb_temp_column = 3
        amb_rh_column = 4
    elif installation_location == 'garage':
        amb_temp_column = 5
        amb_rh_column = 6
    elif installation_location == 'unifinished attic':
        amb_temp_column = 7
        amb_rh_column = 8
    else:
        raise NameError("Error! Only allowed installation locations are living, unfinished basement, garage, unfinished attic. Change the installation location to a valid location")
    mains_temp_column = 9
    
    linenum = 0
    
    ambient_cond_file = open((os.path.join(os.path.dirname(__file__),'data_files','denver_conditions.csv')),'r') #hourly ambient air temperature and RH
    for line in ambient_cond_file:
        if linenum > start_hr and linenum <= (start_hr + num_hrs): #skip header all the way to the start hour but only go as many steps as are needed
            items = line.strip().split(',')
            for b in range(min(num_steps_per_hr,num_steps)): #repeat for however many steps there are in an hr
                Tamb.append([float(items[amb_temp_column])])
                RHamb.append([float(items[amb_rh_column])])
                Tmains.append([float(items[mains_temp_column])])
                b += 1
        linenum += 1
    ambient_cond_file.close()
    
    
    #Read in max and average values for the draw profiles
    linenum = 0
    n_beds = 0
    n_unit = 0
    
    #Total gal/day draw numbers based on BA HSP
    sh_hsp_tot = 14.0 + 4.67 * float(n_br)
    s_hsp_tot = 12.5 + 4.16 * float(n_br)
    cw_hsp_tot = 2.35 + 0.78 * float(n_br)
    dw_hsp_tot = 2.26 + 0.75 * float(n_br)
    b_hsp_tot = 3.50 + 1.17 * float(n_br)
    
    sh_max = np.zeros((5,10))
    s_max = np.zeros((5,10))
    b_max = np.zeros((5,10))
    cw_max = np.zeros((5,10))
    dw_max = np.zeros((5,10))
    sh_sum = np.zeros((5,10))
    s_sum = np.zeros((5,10))
    b_sum = np.zeros((5,10))
    cw_sum = np.zeros((5,10))
    dw_sum = np.zeros((5,10))
    
    sum_max_flows_file = open((os.path.join(os.path.dirname(__file__),'data_files', 'DrawProfiles','MinuteDrawProfilesMaxFlows.csv')),'r') #sum and max flows for all units and # of bedrooms
    for line in sum_max_flows_file:
        if linenum > 0: #this linenum is in min, not hours
            items = line.strip().split(',')
            n_beds = int(items[0]) - 1
            n_unit = int(items[1]) - 1
             #column is unit number, row is # of bedrooms. Taken directly from BEopt
            sh_max[n_beds, n_unit] = float(items[2])
            s_max[n_beds, n_unit] = float(items[3])
            b_max[n_beds, n_unit] = float(items[4])
            cw_max[n_beds, n_unit] = float(items[5])
            dw_max[n_beds, n_unit] = float(items[6])
            sh_sum[n_beds, n_unit] = float(items[7])
            s_sum[n_beds, n_unit] = float(items[8])
            b_sum[n_beds, n_unit] = float(items[9])
            cw_sum[n_beds, n_unit] = float(items[10])
            dw_sum[n_beds, n_unit] = float(items[11])
        linenum += 1
    sum_max_flows_file.close()
    
    linenum = 0
    #Read in individual draw profiles
#    steps_per_year = int(np.ceil(60 * 24 * 365 / timestep_min))
    hot_draw = np.zeros((num_steps,1)) #steps_per_year
    mixed_draw = np.zeros((num_steps,1)) #steps_per_year
    #take into account days shifted
    draw_idx = 60 * 24 * days_shift
    if num_steps <= draw_idx: # if there aren't enough steps being simulated to account for the offset period then just ignore it
        offset = 0
    else:
        offset = draw_idx
        
    draw_profile_file = open((os.path.join(os.path.dirname(__file__),'data_files','DrawProfiles','DHWDrawSchedule_{}bed_unit{}_1min_fraction.csv'.format(n_br,unit))),'r') #minutely draw profile (shower, sink, CW, DW, bath)
    agghotflow = 0.0
    aggmixflow = 0.0
    nbr = n_br - 1 #go back to starting index at zero for python internal calcs
    for line in draw_profile_file:
        if linenum > start_hr*60 and linenum <= start_hr*60+ num_mins: #this linenum is in min
            
            items = line.strip().split(',')
            hot_flow = 0.0
            mixed_flow = 0.0
            
            if items[0] != '':
                sh_draw = float(items[0]) * sh_max[nbr,unit] * (sh_hsp_tot / sh_sum[nbr,unit])
                mixed_flow += sh_draw
            if items[1] != '':
                s_draw = float(items[1]) * s_max[nbr,unit] * (s_hsp_tot / s_sum[nbr,unit])
                mixed_flow += s_draw
            if items[2] != '':
                cw_draw = float(items[2]) * cw_max[nbr,unit] * (cw_hsp_tot / cw_sum[nbr,unit])
                hot_flow += cw_draw
            if items[3] != '':
                dw_draw = float(items[3]) * dw_max[nbr,unit] * (dw_hsp_tot / dw_sum[nbr,unit])
                hot_flow += dw_draw
            if items[4] != '':
                b_draw = float(items[4]) * b_max[nbr,unit] * (b_hsp_tot / b_sum[nbr,unit])
                mixed_flow += b_draw
            agghotflow += hot_flow
            aggmixflow += mixed_flow
#                aggregate whenever the linenum is a multiple of timestep_min. Each increment in lineum represents one minute. Timestep_min is the number of minutes per timestep
            if timestep_min >= 1: # aggregate if timesteps are >= 1 minute
                if linenum % timestep_min == 0: 
                    hot_draw[offset] = agghotflow
                    mixed_draw[offset] = aggmixflow
                    agghotflow = 0
                    aggmixflow = 0
                    draw_idx += 1
            elif timestep_min < 1: # repeat the value if timesteps are < 1 minute
#                    print('len draws',len(hot_draw))
#                    if linenum == 1:
#                        hot_draw[offset] = hot_flow #assume hot_draw = 0 up until draw_idx timestep
#                        mixed_draw[offset] = mixed_flow #assume mixed_draw = 0 up until draw_idx timestep
                    
                for c in range(min(steps_per_min,num_steps)): #repeat for however many steps there are in a minute 
#                        hot_draw = np.append(hot_draw,hot_flow)
#                        mixed_draw = np.append(mixed_draw,mixed_flow)
                    hot_draw[offset + c] = hot_flow #assume hot_draw = 0 up until draw_idx timestep
                    mixed_draw[offset + c] = mixed_flow
                    c += 1
#                    print('len hot_draw', len(hot_draw))    
        linenum += 1
#            if draw_idx >= steps_per_year:
#                draw_idx = 0
    draw_profile_file.close()
    return Tamb, RHamb, Tmains, hot_draw, mixed_draw