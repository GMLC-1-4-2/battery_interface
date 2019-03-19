# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 15:07:49 2018
For GMLC 1.4.2, fleet Virtual Battery Model for HVACs
Based on a valided 4R4C building thermal model

Last update: 03/18/2019
Version: 1.0

@author: Jin Dong (ORNL), Jeffrey Munk (ORNL), Teja Kuruganti (ORNL)
"""

# code needed for GLOBAL fleet_interface
import sys
from os.path import dirname, abspath, join
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))
################################################################

from configparser import ConfigParser
from datetime import datetime, timedelta
# This is the actual building thermal and HVAC models
#import build_model as bm
from build_model import BuildingModel
from build_model import AC

#from HVACFleet import FleetResponse   #HVACFleet
from fleet_interface import FleetInterface
from fleet_response import FleetResponse
from fleets.HVAC_fleet.load_config import LoadConfig
# from frequency_droop import FrequencyDroop

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import random
import pandas as pd
import scipy as sp
import time
import csv

#INPUTS
shortcycle=5*60 # minutes  time that AC unit has to stay off before turning back on
minrun=1*60 # minutes  minimum runtime for unit
Twb_assumed=16.666667  #assumed indoor wet bulb temperature

ts = 1.0 # seconds, must be a divisor of 60, time step
shortcycle_ts=int(round(shortcycle/ts,0))  #number of time steps during short cycle timer
minrun_ts=int(round(minrun/ts,0))
Tset = 23.0 #celcius  cooling set point
deadband=0.5 #celcius cooling dead band

#Column names for weather input data
class c():
    COL_TOUT='Dry-bulb (C)'
    COL_H='Hconvection'
    COL_QIHL='QIHL (W)'
    COL_RADW='Radwall (W/m^2)'
    COL_RADR='Radroof (W/m^2)'
    COL_RADWIN='Radwindow (W/m^2)'
    COL_DATETIME='Date/Time'
    
#Coefficients that define AC capacity and efficiency as a function of OD dry bulb and ID wet bulb (Biquadratic used in EnergyPlus, coefficients from BEopt 2.7)
class AC:
    C1=1.557359706
    C2=-.074448169
    C3=.003098597
    C4=0.001459579
    C5=-4.1148E-5
    C6=-.000426714
    C7=-.35044769
    C8=0.116809893
    C9=-.00339951
    C10=-.00122609
    C11=.000600809
    C12=-.00046688
    def __init__(self, Qrated, EIRrated):
        self.Qrated=Qrated
        self.EIRrated=EIRrated
    
#Total cooling capacity
def Capacity(AC,Tout,Twb=Twb_assumed):
    return((AC.C1+AC.C2*Twb+AC.C3*Twb*Twb+AC.C4*Tout+AC.C5*Tout*Tout+AC.C6*Tout*Twb)*AC.Qrated)
#EIR for cooling    
def EIR(AC,Tout,Twb=Twb_assumed):
    return((AC.C7+AC.C8*Twb+AC.C9*Twb*Twb+AC.C10*Tout+AC.C11*Tout*Tout+AC.C12*Tout*Twb)*AC.EIRrated)

#SHR equation derived from apparatus dew point (ADP) method used by EnergyPlus for BEopt 2.7 AC    
def SHR(Tout,Tdb,Twb):
    return(0.64613+0.003183*Tdb-.08153*Twb+.059996*Tdb)

#Building characteristics    
class building:
    def __init__(self,T_in,T_mass,T_wall,T_attic,Rwall=0.00852, Rattic=0.03441,Rwin=0.00702,SHGC=0.4,Cwall=6719515.27,Cin=8666569.0,C1=0.73244,C2=0.49534,C3=0.05,Cattic=501508.7,Rroof=0.002,Cmass=29999128.0,Rmass=.00661,Sp1=0.93,Sp2=0.10006,Sp3=0.92997, Qrated=14600, EIRrated=0.31019, TinWB=Twb_assumed,Initial_On=0):
        self.T_in=T_in
        self.T_mass=T_mass
        self.T_wall=T_wall
        self.T_attic=T_attic
        self.Rwall=Rwall
        self.Rattic=Rattic
        self.Cwall=Cwall
        self.Cin=Cin
        self.C1=C1
        self.C2=C2
        self.C3=C3
        self.Cattic=Cattic
        self.Rroof=Rroof
        self.Cmass=Cmass
        self.Rmass=Rmass
        self.Sp1=Sp1
        self.Sp2=Sp2
        self.Sp3=Sp3
        self.Qrated=Qrated
        self.EIRrated=EIRrated
        self.TinWB=TinWB
        self.Rwin=Rwin
        self.SHGC=SHGC
        self.Initial_On=Initial_On


class HVACFleet(FleetInterface):   #FleetInterface
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """
    def __init__(self, GridInfo, ts):
        """
        for battery def __init__(self, GridInfo,**kwargs):
        old: (self, Steps = 100, Timestep = 10, P_request = 0, Q_request = 0, forecast = 0, StartHr = 40)
        """
        # Location of working path
        base_path = dirname(abspath(__file__))
        
        # Read config file
        config = ConfigParser()
        config.read(join(base_path, 'config.ini'))
       
        # Load config file and store data in a dataframe
        LC = LoadConfig(config)
        self.df_VehicleModels = LC.get_config_models()
        
        # Run baseline power to store baseline power and SOC if parameters 
        # of the fleet are changed. ONLY ASSIGN TRUE IF YOU CHANGE THE 
        # PARAMETERS OF THE FLEET AS IT WILL DRAMATICALLY INCREASE THE CPU TIME
        self.run_baseline = LC.get_run_baseline()
        # Establish the properties of the grid on which the fleet is connected on
        self.grid = GridInfo
        # Get cur directory
        base_path = dirname(abspath(__file__))

        # Total number of HVACs
        self.numHVAC = self.df_HVACModels['Total_HVACs'].sum()

        # assign full SoC for the fleet
        self.SoC = [[0.8 for x in range(1)] for y in range(self.numHVAC)]
        
        # #%% Frequency-watt parameters
        # FrequencyWatt='Frequency Watt'
        # self.db_UF=float(self.config.get(FrequencyWatt,'db_UF'))
        # self.db_OF=float(self.config.get(FrequencyWatt,'db_OF'))
        # self.k_UF=float(self.config.get(FrequencyWatt,'k_UF'))
        # self.k_OF=float(self.config.get(FrequencyWatt,'k_OF'))

        # generate random houses based on the validated building model
        # varying R, C values by some coefficients
        # represents low efficiency, normal efficiency and high efficiency houses (corresponding to different envelope/insulation parameters)
        # for envelope type, location and max. number of service calls need to specify discrete values and randomly sampled to get a desired distribution 
        # self.numHVAC = 200 # number of HVACs in fleet, default 200
#        Steps = 60 #num steps in simulation 6 steps = 1 hour 1 day = 24*6 = 144
#        lengthRegulation = 20 # num of 4-second steps for regulation signal
#        addshedTimestep = 10 # minutes, NOTE, MUST BE AN INTEGER DIVISOR OF 10. Acceptable numbers
        # self.ts = ts  # mins/interval of discrete control

        # How to calculate effective fleet rating: this is going to be poorly
        # met because it does not consider random availability of the fleet. 
        # However this seems to be the best approximation
        
        self.fleet_rating = self.numHVAC * 3.5  # unit power is 3.5 kw, approximate 25% can provide service   

        # Weight used to scale the service request
        self.service_weight = LC.get_service_weight()    

        """
        Can this fleet operate in autonomous operation?
        """
        
        # Locations of the subfleets: suppose that you only have one location
        self.location = np.random.randint(0,1,self.numHVAC)
        
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
            self.db_UF_subfleet = np.random.uniform(low = self.db_UF[0], high = self.db_UF[1], size = (self.numHVAC, ))
            self.db_OF_subfleet = np.random.uniform(low = self.db_OF[0], high = self.db_OF[1], size = (self.numHVAC, ))
        
        # Impact metrics of the fleet
        # End of life cost
        metrics = LC.get_impact_metrics_params()
        self.ave_Tin = metrics[0]
        # Cylce life
        self.cycle_life = metrics[1]
        # State of health of the battery equivalent model
        self.unmet_hours = metrics[2]
        # self.soh = np.repeat(metrics[2], self.N_SubFleets)

       
        ########### initial indoor temperatures and SoC
        self.TinInitialMean = 23.67 #deg C
        self.TinInitialStddev = 0.3 #deg C
        
        # initial temperature setpoints
        self.TsetInitialMean = 23.0 #deg C  convert from 80F+-4
        self.TsetInitialStddev = 1   #2.22 #deg C
        
        self.minSOC = 0.1 # minimum SoC for aggregator to call for shed service
        self.maxSOC = 0.9 # minimum SoC for aggregator to call for add service
        
        self.minCapacityAdd = 150 #W-hr, minimum add capacity to be eligible for add service
        self.minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
     
        # Varying parameters for different Envelopes
        # R value of the exterior wall
        
        self.RextMasterList = [0.00852, 0.00852, 0.00852, 0.00852, 0.00852, 0.00639,  0.00639, 
                  0.00639, 0.01065, 0.01065 ]   #50% Normal, 30% Low-efficiency, 20% High-efficiency
        # R value of the attic
        self.RatticMasterList = [0.03441, 0.03441, 0.03441, 0.03441, 0.0258075, 0.0258075, 
                    0.0258075, 0.0430125,  0.0430125, 0.0430125, ] #40% Normal, 30% Low-efficiency, 30% High-efficiency
        # C value of thermal mass
        self.CmassMasterList = [29999127.91, 29999127.91, 29999127.91, 29999127.91, 29999127.91,
                   29999127.91, 37498909.89, 37498909.89, 37498909.89, 44998691.87]  #30% Normal, 60% Low-efficiency, 10% High-efficiency
        #  Typical US nationwide climate locations
        self.ClimateMasterList = ['Miami', 'Phoenix', 'Atlanta', 'Atlanta', 'Las Vegas', 'Denver',  
                             'Denver', 'Atlanta', 'Miami', 'Minneapolis'] # 20% Miami
        # 30% Atlanta; 20% Denver, 10% for Phoneix, Vegas and Minneapolis
        
        self.MaxServiceCallMasterList = [30, 20, 20, 10, 15, 25, 5, 15, 30] # this is the max number of monthly service calls for load add/shed.
        
         ########################################################################
        
        # Initialize timestamps and local times of the class for future calculations
        self.initial_ts = ts # time stamp to start the simulation
        self.ts = ts
        self.initial_time = self.get_time_of_the_day(ts)
        self.time = self.get_time_of_the_day(ts)
        self.dt = 1       # time step (in seconds)

        
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
        This function takes the fleet request and repackages it for the interal run function
        :param fleet_request: an instance of FleetRequest
        :return fleet_response: an instance of FleetResponse
        ## Follow the example of EV
        """
        ts = fleet_request.ts_req   # starting time
        dt = int(fleet_request.sim_step.total_seconds())   #fleet_request.sim_step  # Sim_step is how long a simulation time step
        p_req = fleet_request.P_req
        q_req = fleet_request.Q_req

        # call run function with proper inputs
        fleet_response = self.run(p_req, q_req, self.SOC, self.time, dt, ts)

        return fleet_response

    # Example code for Frequency Watt Function (following battery intvrter)
    '''
     However, reactive power is not modeled in current model.
     So, we skipped the VVO function.
    '''
    
    def frequency_watt(self, p_req = 0,ts=datetime.utcnow(),location=0):
        """
        This function takes the requested power, date, time, and location
        and modifys the requested power according to the configured FW21 
        :param p_req: real power requested, ts:datetime opject,
               location: numerical designation for the location of the BESS
        :return p_mod: modifyed real power based on FW21 function
        """
        f = self.grid.get_frequency(ts,location)

        if f < 60 - db_UF:
            p_mod = 0
        elif f > 60 + db_OF:
            p_mod = p_req
        else:
            p_mod = p_prev

        return p_mod

    def update_soc_due_to_frequency_droop(self, initSOC, subfleet_number, p_subfleet, dt):
        """
        This method returns the modified state of charge of each subfleet 
        due to frequency droop in the grid
        """
        p_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet_number]],
                                     self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet_number]],
                                     self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet_number]],
                                     self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]], p_subfleet)
        R = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['R_SOC_1'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['R_SOC_2'][self.SubFleetId[subfleet_number]], initSOC)
        v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['V_SOC_1'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['V_SOC_2'][self.SubFleetId[subfleet_number]], 
                                    self.df_VehicleModels['Number_of_cells'][self.SubFleetId[subfleet_number]],initSOC,0,0)
        
        ibat_charging = self.current_charging(v_oc,R,p_dc) 
        Ah_rate = ibat_charging/3600
        charge_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet_number]]
        SOC_update = initSOC + charge_rate*dt
        
        if SOC_update > 1:
            p_subfleet = 0
            SOC_update = initSOC

        return p_subfleet*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet_number]])/1000, SOC_update

    # Example code for VVO
    '''
     However, reactive power is not modeled in current model.
     So, we skipped the VVO function.
    '''
    # # Rewrite following battery inverter model
    # def forecast(self, fleet_requests):
    #     responses = []
    #     for request in fleet_requests:
    #         response = self.run(request, forecast=1)
    #         responses.append(response)

    #     return responses

    def run(self, P_req, Q_req, initSOC, t, dt, ts): 
        #ExecuteFleet(self, Steps, Timestep, P_request, Q_request, forecast):
        # run(self, P_req=[0], Q_req=[0], ts=datetime.utcnow(), del_t=timedelta(hours=1)):    
        
        # Give the code the capability to respond to None requests
        if P_req == None:
            P_req = 0
        if Q_req == None:
            Q_req = 0

        ##################################     
        #    Initializing lists to be saved to track indivisual HVAC performance over each timestep

        # Randomly set up and mix the HVAC fleet
        # Random seed for regenerating the same result
        self.seed = 0
        np.random.seed(self.seed)

        # generate distribution of initial HVAC fleet states. this means Rext, Rattic, Cmass,
        # profile for the yr for each building in fleet, this will be imported later, just get something reasonable here
        # random initial temperatures (total 4 states in the 4R4C Model)
        TinInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        TwallInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        TmassInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        TatticInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        
        # random Temperature setpoints
        TsetInitial=np.random.normal(self.TsetInitialMean, self.TsetInitialStddev,self.numHVAC)
        
        # sampling from houses with different envelope efficiencies
        Rext = [random.choice(self.RextMasterList) for n in range(self.numHVAC)]
        Rattic = [random.choice(self.RatticMasterList) for n in range(self.numHVAC)]
        Cmass = [random.choice(self.CmassMasterList) for n in range(self.numHVAC)]
        Location = [random.choice(self.ClimateMasterList) for n in range(self.numHVAC)]
        
        MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numHVAC)]    
        
        ###########################################################################       
        #   for calculating weather conditions needed by building model
        #   V = [ Tsol_w,   QIHL_i,   Qsolar_i;   Tsol_r,   QIHL_mass,   Qsolar_mass] 
        # load the weather profile

        #read in weather data and increase resolution to match time step of simulation
        # # measurement = pd.read_excel('./data_file/Vegas_TMY3_July_10mins.xlsx')   # or Min5_data_vegas.xlsx
        # inputs = pd.read_csv('./data_file/LasVegas_HighCDD.csv', sep=',',skipfooter=48,engine='python')
        # inputs[c.COL_DATETIME] = pd.to_datetime(inputs[c.COL_DATETIME])
        # inputs = inputs.set_index(c.COL_DATETIME)
        # inputs_ts = inputs.resample(str(ts)+'T').interpolate()         # resample T means minutes, change to seconds 
        
        # #calculate T solar for walls and roofs
        # #TODO: make house specific
        # inputs_ts['Tsolw']=inputs_ts[c.COL_TOUT]+inputs_ts[c.COL_RADW]*0.3/inputs_ts[c.COL_H]
        # inputs_ts['Tsolr']=inputs_ts[c.COL_TOUT]+inputs_ts[c.COL_RADR]*0.8/inputs_ts[c.COL_H]

        measurement = pd.read_excel('./data_file/Vegas_TMY3_July_10mins.xlsx')   # or Min5_data_vegas.xlsx
        #        measurement_or['Date/Time']=pd.to_datetime(measurement_or['Date/Time'])
        #        measurement_or = measurement_or.set_index('Date/Time')
        #        measurement = measurement_or.resample(str(ts)+'T').interpolate()  # interpolate from Hour to 10 min
        measurement = np.matrix(measurement)
        # Index of each outdoor disturbance in the imported file
        outdoor_temp_idx = 0
        rad_wall_idx = 8
        convect_heat_idx = 11
        #  IHL_idx = 7
        rad_window_idx = 10
        rad_roof_idx = 9
        
        aw = 0.3
        ar = 0.8
        SHGC = 0.56
        Awin = 25.76  # window size m^2
        Sp1=0.93
        Sp2=0.10006
        Sp3=0.92997
    
        ############## Overall disturbance signal ###############
        # V = [Tsol_W, QIHL_i, Qsolar_i, Tsol_R, QIHL_mass, Qsolar_mass]
        # Measurements of disturbances
        rad_wall = measurement[:, rad_wall_idx]
        convect_heat = measurement[:, convect_heat_idx]
        rad_window = measurement[:, rad_window_idx]
        rad_roof = measurement[:, rad_roof_idx] 

        # Calculate T sol for walls
        temp_sol_W10 = 0.3*np.divide(rad_wall, convect_heat) 
        # Calculate T sol for attic
        temp_sol_R10 = 0.8*np.divide(rad_roof,convect_heat)            
        # solar through windows
        Qsolar = np.multiply(np.multiply(rad_window, Awin), SHGC)
    
        # Separate Qsolar into internal and on mass               
        Qsolar_i10 = Sp3*Qsolar
        Qsolar_mass10 = (1-Sp3)*Qsolar  

        # interpolate the data from 10 mins to desired time resolution in seconds
        (Qsolar_i, Qsolar_mass, temp_sol_W, temp_sol_R) = get_inputs(Qsolar_i10, Qsolar_mass10, temp_sol_W10, temp_sol_R10, timestep_s, ts)  

        # Load the other disturbance signals by randomly sampling with different weather conditions     
        Tamb = []
        Tsol_W = []
        Tsol_R = []
        IHL = []

        for a in range(self.numHVAC):             
            if a <= (self.MaxNumMonthlyConditions-1): #if numHVAC > MaxNumAnnualConditions just start reusing older conditions to save computational time               
      
                (tamb, IHL_s) = get_daily_conditions(Location[a], del_t, ServiceRequest.Steps, ts)
                
                tsol_W = tamb + temp_sol_W
                tsol_R = tamb + temp_sol_R

                Tamb.append(tamb)
                Tsol_W.append(tsol_W)
                Tsol_R.append(tsol_R)
                IHL.append(IHL_s)
 
            else: #start re-using conditions
                Tamb.append(Tamb[a - self.MaxNumMonthlyConditions][:])
                Tsol_W.append(Tsol_W[a - self.MaxNumMonthlyConditions][:])
                Tsol_R.append(Tsol_R[a - self.MaxNumMonthlyConditions][:])
                IHL.append(IHL[a - self.MaxNumMonthlyConditions][:])
        
        QIHL_i = np.multiply(Sp1, IHL)
        QIHL_mass = np.multiply(1-Sp1, IHL)
        Tsol_W = np.array(Tsol_W)
        Tsol_R = np.array(Tsol_R)        
        
        # Just take forecast of IHL as an example, it can be easily extended to solar irradiation
        IHL_fleet = sum(IHL)# this sums all rows, where each row is an HVAC, so gives the fleet sum of IHL at each step
        IHL_fleet_ave = IHL_fleet/self.numHVAC  # this averages all rows, where each row is an HVAC, so gives the fleet average of IHL at each step

        Steps = 1
        Tset = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Tin = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Twall = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Tmass = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Tattic = [[0 for x in range(Steps)] for y in range(self.numHVAC)]

        SoC = initSOC

        AvailableCapacityAdd = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        AvailableCapacityShed = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        ServiceCallsAccepted = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        ServiceProvided = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        IsAvailableAdd = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        IsAvailableShed = [[0 for x in range(Steps)] for y in range(self.numHVAC)]

        elementOn = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        lockon = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        lockoff = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        cycle_off_base = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        cycle_on_base = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        cycle_off_grid = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        cycle_on_grid = [[0 for x in range(Steps)] for y in range(self.numHVAC)]

        # TotalServiceProvidedPerHVAC = [0 for y in range(self.numHVAC)]
        TotalServiceProvidedPerTimeStep = [0 for y in range(Steps)]
        
        # MaxServiceAddedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]
        # MaxServiceShedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]

        TotalServiceCallsAcceptedPerHVAC = [0 for y in range(self.numHVAC)]    
   
        SoCInit = [0.5 for y in range(self.numHVAC)]

        AvailableCapacityAddInit = [0 for y in range(self.numHVAC)]
        AvailableCapacityShedInit = [0 for y in range(self.numHVAC)]

        IsAvailableAddInit = [1 for y in range(self.numHVAC)]
        IsAvailableShedInit = [1 for y in range(self.numHVAC)]
        
        P_req = 0

        ##############################################################################################################
 
        #    Initializing the building HVAC models
        #    Get the baseline power
        hvacs = [BuildingModel(Tamb[0], Tsol_W[0], QIHL_i[0], Qsolar_i[0], Tsol_R[0],
                               QIHL_mass[0],Qsolar_mass[0], P_req, Rext[number], 
                               Rattic[number], Cmass[number], 0, MaxServiceCalls[number], self.ts) for number in range(self.numHVAC)]
        
        FleetResponse.P_service = 0
        FleetResponse.P_service_max = 0
        FleetResponse.P_service_min = 0
        FleetResponse.P_togrid = 0
        FleetResponse.P_togrid_max = 0
        FleetResponse.P_togrid_min = 0
        FleetResponse.P_forecast = 0
        FleetResponse.E = 0
        FleetResponse.C = 0

        P_request_perHVAC = P_req / self.numHVAC # this is only for the first step
        #        print(P_request_perWH)
        
        FleetResponse.Q_togrid = 0
        FleetResponse.Q_service = 0
        FleetResponse.Q_service_max = 0
        FleetResponse.Q_service_min = 0
        FleetResponse.Q_togrid_min = 0  
        FleetResponse.Q_togrid_max = 0
        Eloss = 0
        Edel = 0 
        
        FleetResponse.Q_dot_up = 0
        FleetResponse.Q_dot_down = 0
        FleetResponse.P_dot_up = 0
        FleetResponse.P_dot_down = 0
   
        # run through fleet once as a forecast just to get initial conditions
        number = 0
        for h in hvacs:
            fcst = 1   #  setting the forecast to 1 for this initialization only
            response = h.execute(TinInitial[number], TwallInitial[number], TmassInitial[number], TatticInitial[number], TsetInitial[number], Tamb[number][0], Tsol_W[number][0], QIHL_i[number][0], Qsolar_i[0], Tsol_R[number][0], QIHL_mass[number][0], Qsolar_mass[0], Rext[number], Rattic[number], Cmass[number], P_request_perHVAC, ServiceRequest.Timestep, IHL_fleet_ave[0], elementOn[number][0], lockon[number][0], lockoff[number][0], cycle_off_base[number][0], cycle_on_base[number][0], cycle_off_grid[number][0], cycle_on_grid[number][0]) #forecast = 1
            number += 1
           
        for step in range(1):    
            number = 0
            servsum = 0
            servmax = 0
            servmax2 = 0
            NumDevicesToCall = 0
            laststep = step - 1
    
        #  decision making about which HVAC to call on for service, check if available at last step, if so then 
        #  check for SoC > self.minSOC and Soc < self.maxSOC
            if step == 0: #use the initialized values to determine how many devices are available
                for n in range(self.numHVAC):
                    if P_request_perHVAC < 0 and IsAvailableAddInit[n] > 0 and SoCInit[n] < self.maxSOC and AvailableCapacityAddInit[n] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perHVAC > 0 and IsAvailableShedInit[n] > 0 and SoCInit[n] > self.minSOC and AvailableCapacityShedInit[n] > self.minCapacityShed:
                        NumDevicesToCall += 1
            elif step > 0: #use the last temperature to determine how many devices are available
                for n in range(self.numHVAC):
                    if P_request_perHVAC < 0 and IsAvailableAdd[n][laststep] > 0 and SoC[n][laststep] < self.maxSOC and AvailableCapacityAdd[n][laststep] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perHVAC > 0 and IsAvailableShed[n][laststep] > 0 and SoC[n][laststep] > self.minSOC and AvailableCapacityShed[n][laststep] > self.minCapacityShed:
                        NumDevicesToCall += 1          
      
            P_request_perHVAC =  P_req[step] / max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

            #################################      
            for hvac in hvacs: #loop through all HVACs
                if step == 0:
                    ### call hvac.execute

                    # response = tin, twall, tmass, tattic, tset, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed
                    response = hvac.execute(TinInitial[number], TwallInitial[number], TmassInitial[number], TatticInitial[number],TsetInitial[number], Tamb[number][0], Tsol_W[number][0], QIHL_i[number][0], Qsolar_i[0], Tsol_R[number][0], QIHL_mass[number][0], Qsolar_mass[0], Rext[number], Rattic[number], Cmass[number],  0, del_t, IHL_fleet_ave[0], elementOn[number][0], lockon[number][0], lockoff[number][0], cycle_off_base[number][0], cycle_on_base[number][0], cycle_off_grid[number][0], cycle_on_grid[number][0])
                
                elif step>0 and  P_req<=0 and IsAvailableAdd[number][laststep] > 0 :
                # For step >=1, can use last step temperature...
                    TsetLast = Tset[number][laststep]
                    TinLast = Tin[number][laststep]     
                    TwallLast = Twall[number][laststep] 
                    TmassLast = Tmass[number][laststep] 
                    TatticLast = Tattic[number][laststep] 
             
                    response = hvac.execute(TinLast, TwallLast, TmassLast, TatticLast, TsetLast, Tamb[number][step], Tsol_W[number][step], QIHL_i[number][step], Qsolar_i[step], Tsol_R[number][step], QIHL_mass[number][step], Qsolar_mass[step], Rext[number], Rattic[number], Cmass[number], P_request_perHVAC, del_t, IHL_fleet_ave[min([step,ServiceRequest.Steps-1])], elementOn[number][step], lockon[number][step], lockoff[number][step], cycle_off_base[number][step], cycle_on_base[number][step], cycle_off_grid[number][step], cycle_on_grid[number][step])
                    P_req[step] =  P_req[step] - response.Eservice

                elif step>0 and  P_req[step]>0 and IsAvailableShed[number][laststep] > 0 :
                # For step >=1, can use last step temperature...
                    TsetLast = Tset[number][laststep]
                    TinLast = Tin[number][laststep]     
                    TwallLast = Twall[number][laststep] 
                    TmassLast = Tmass[number][laststep] 
                    TatticLast = Tattic[number][laststep] 
             
                    response = hvac.execute(TinLast, TwallLast, TmassLast, TatticLast, TsetLast, Tamb[number][step], Tsol_W[number][step], QIHL_i[number][step], Qsolar_i[step], Tsol_R[number][step], QIHL_mass[number][step], Qsolar_mass[step], Rext[number], Rattic[number], Cmass[number], P_request_perHVAC, del_t, IHL_fleet_ave[min([step,ServiceRequest.Steps-1])], elementOn[number][step], lockon[number][step], lockoff[number][step], cycle_off_base[number][step], cycle_on_base[number][step], cycle_off_grid[number][step], cycle_on_grid[number][step])
                    P_req[step] =  P_req[step] - response.Eservice    
                # break

                else:
                    TsetLast = Tset[number][laststep]
                    TinLast = Tin[number][laststep]     
                    TwallLast = Twall[number][laststep] 
                    TmassLast = Tmass[number][laststep] 
                    TatticLast = Tattic[number][laststep] 
             
                    response = hvac.execute(TinLast, TwallLast, TmassLast, TatticLast, TsetLast, Tamb[number][step], Tsol_W[number][step], QIHL_i[number][step], Qsolar_i[step], Tsol_R[number][step], QIHL_mass[number][step], Qsolar_mass[step], Rext[number], Rattic[number], Cmass[number], 0, del_t, IHL_fleet_ave[min([step,ServiceRequest.Steps-1])], elementOn[number][step], lockon[number][step], lockoff[number][step], cycle_off_base[number][step], cycle_on_base[number][step], cycle_off_grid[number][step], cycle_on_grid[number][step])
                # assign returned parameters to associated lists to be recorded
                Tset[number][step] = response.Tset
                Tin[number][step] = response.Tin
                Twall[number][step] = response.Twall
                Tmass[number][step] = response.Tmass
                Tattic[number][step] = response.Tattic

                elementOn[number][step] = response.ElementOn
                lockon[number][step] = response.lockon
                lockoff[number][step]  = response.lockoff
                cycle_off_base[number][step] = response.cycle_off_base
                cycle_on_base[number][step] = response.cycle_on_base
                cycle_off_grid[number][step] = response.cycle_off_grid
                cycle_on_grid[number][step] = response.cycle_on_grid
                
                SoC[number][step] = response.SOC
                IsAvailableAdd[number][step] = response.IsAvailableAdd
                IsAvailableShed[number][step] = response.IsAvailableShed
                
                elementOn[number][step] = response.ElementOn
                AvailableCapacityAdd[number][step] = response.AvailableCapacityAdd 
                AvailableCapacityShed[number][step] = response.AvailableCapacityShed 
                ServiceCallsAccepted[number][step] = response.ServiceCallsAccepted
                ServiceProvided[number][step] += response.Eservice
                
                servsum += response.Eservice       

                #  TotalServiceProvidedPerHVAC[number] = TotalServiceProvidedPerHVAC[number] + ServiceProvided[number][step]
                #  P_injected += eused
                #  P_injected_max += pusedmax
                #  servmax += availableCapacityAdd*1e3
                #  servmax2 += availableCapacityShed*1e3                               
                
                FleetResponse.P_togrid += response.Eused
                FleetResponse.P_togrid_max += response.PusedMax
                FleetResponse.P_togrid_min += response.PusedMin                
                FleetResponse.P_service += response.Eservice                
                number += 1  # go to next building

                # Available Energy stored at the end of the most recent timestep
                # FleetResponse.E += response.Estored
                FleetResponse.E = 0
                FleetResponse.C += response.SOC / (self.numHVAC)
                FleetResponse.P_service_max += response.AvailableCapacityShed # NOTE THIS ASSUMES THE MAX SERVICE IS LOAD SHED
                
            # FleetResponse.P_dot_up = FleetResponse.P_togrid_max / ServiceRequest.Timestep.seconds
            FleetResponse.P_dot = FleetResponse.P_togrid / ServiceRequest.Timestep.seconds
            FleetResponse.P_service_min  = 0
            
            # FleetResponse.Q_dot_down     = 0
            FleetResponse.dT_hold_limit  = None
            FleetResponse.T_restore      = None
            FleetResponse.Strike_price   = None
            FleetResponse.SOC_cost       = None

            FleetResponse.ts = ts

            TotalServiceProvidedPerTimeStep[step] = -1.0*servsum   # per time step for all hvacs  -1.0*
            
            """
            Modify the power and SOC of the different subfeets according 
            to the frequency droop regulation according to IEEE standard
            """
            for subfleet in range(self.numHVAC):
                if self.state_of_the_subfleet(t,subfleet) == 'home after schedule':
                    if self.FW21_Enabled and self.is_autonomous:
                        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet]]
                        p_prev = power_subfleet[subfleet]*1000/(self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet]]))
                        power_subfleet[subfleet] = self.frequency_watt(power_ac,
                                                                       p_prev,
                                                                       self.ts,
                                                                       self.location[subfleet],
                                                                       self.db_UF_subfleet[subfleet],
                                                                       self.db_OF_subfleet[subfleet])
                        power_subfleet[subfleet], SOC_step[subfleet] = self.update_soc_due_to_frequency_droop(initSOC[subfleet],
                                                                                                              subfleet,
                                                                                                              power_subfleet[subfleet],
                                                                                                              dt)
                    else:
                        break

            # Demand of power
            power_demanded = np.sum(power_subfleet, axis = 0)
            
            # # Calculate maximum power that can be injected to the grid -> all the right away chargers are turned on
            # for subfleet in range(self.N_SubFleets):
            #     if self.state_of_the_subfleet(t,subfleet) == 'home after schedule':  
            #         if self.monitor_strategy[subfleet] == 'right away':
            #             SOC_check, power_subfleet[subfleet] = self.start_charging_right_away_strategy(subfleet, initSOC[subfleet], dt)
            #             if SOC_check > 1:
            #                 power_subfleet[subfleet] = 0
        
            # # # Maximum demand of power
            # # max_power_demanded = np.sum(power_subfleet, axis = 0)    
        
        self.SOC = SOC_step
        self.time = t + dt
        self.ts = self.ts + timedelta(seconds = dt)
        # Restart time if it surpasses 24 hours
        if self.time > 24*3600:
            self.time = self.time - 24*3600
        
        # return TotalServiceProvidedPerTimeStep, MaxServiceAddedPerTimeStep, MaxServiceShedPerTimeStep, P_injected, Q_injected, P_service, Q_service, P_injected_max, Q_service_max, P_forecast, Q_forecast
        return FleetResponse 
      
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
        SOC = self.soc 

        TinR = self.Tin
        TwallR = self.Twall
        TmassR = self.Tmass
        TatticR = self.Tattic

        # Iterate and process each request in fleet_requests
        for req in requests:
            ts = req.ts_req
            dt = int(req.sim_step.total_seconds())
            p_req = req.P_req
            q_req = req.Q_req
            res = self.simulate(p_req, q_req, self.SOC, self.time, dt, ts)

            responses.append(res)
                    
        # reset the model
        self.soc = SOC 
        self.Tin = TinR
        self.Twall = TwallR
        self.Tmass = TmassR
        self.Tattic = TatticR
  
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
        
        # base_path = dirname(abspath(__file__))
        # path = join(base_path,'data')
        
        # df_soc.to_csv(join(path, r'SOC_baseline.csv'), index = False)
        # df_power.to_csv(join(path, r'power_baseline.csv'), index = False)
        # print("Exported")

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
       
        for day in range(n_days_base):
            print("Day %i" %(day+1))
            
            #initialize dataframes
            timeB = np.array(np.arange(0,60*60*24,ts))
            plot_timeB = np.array(np.arange(0,24,ts/3600))

            Tin=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            Tmass=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            Twall=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            Tattic=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            ACstatus=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            dTin=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            dTmass=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            dTwall=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            dTattic=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            Power=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            cycles=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            SOC=pd.DataFrame(data=0,index=timeB,columns=range(0,numHVAC))
            
            num_homes = numHVAC
            
            
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
            for i in range(0,int(1440*60/ts)):
                for j in range(0,num_homes):                    
                    
                    if i>0:   #initialize AC status for each timestep to prior state
                        ACstatus.iloc[i,j]=ACstatus.iloc[i-1,j]
                    else:     #Set AC status based on file input for first timestep
                        ACstatus.iloc[i,j]=b[j].Initial_On
                    if Tin.iloc[i,j]>=Tset+deadband and ACstatus.iloc[max(i-shortcycle_ts,0):i,j].sum()==0:  #if temp is above deadband and unit has not run in past duration corresponding to short cycle timer turn on unit
                        ACstatus.iloc[i,j]=1.0
                    if Tin.iloc[i,j]<=Tset-deadband:    #if temperature is below bottom deadband, turn off unit
                        ACstatus.iloc[i,j]=0.0
                    #count cycles
                    if i>0 and ACstatus.iloc[i-1,j]==1.0 and ACstatus.iloc[i,j]==0.0:
                        cycles.iloc[i,j]=1.0
                        
                    #calculate power use for each AC based on status
                    Power.iloc[i,j]=ACstatus.iloc[i,j]*Capacity(ac[j],inputs_ts[c.COL_TOUT][i],b[j].TinWB)*EIR(ac[j],inputs_ts[c.COL_TOUT][i],b[j].TinWB)
                    
                    # calculate SOC for each AC
                    SOC.iloc[i,j] = (Tset+deadband - Tin.iloc[i,j])/(2*deadband)

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
    
    
    # def output_impact_metrics(self):   
    #     impact_metrics_DATA = [["Impact Metrics File"],
    #                             ["state-of-health", "initial value", "final value", "degradation cost"]]
    #     for i in range(self.num_of_devices):
    #         impact_metrics_DATA.append(["battery-"+str(i), str(self.soh_init), str(self.soh[i]), str((self.soh_init-self.soh[i])*self.eol_cost/100)])

    #     total_cost = sum((self.soh_init-self.soh)*self.eol_cost/100)
    #     impact_metrics_DATA.append(["Total degradation cost:", str(total_cost)])

    #     with open('impact_metrics.csv', 'w') as csvfile:
    #         writer = csv.writer(csvfile)
    #         writer.writerows(impact_metrics_DATA)     

    #     pass

    # def change_config(self, fleet_config):
    #     """
    #     This function updates the fleet configuration settings programatically.
    #     :param fleet_config: an instance of FleetConfig
    #     """

    #     # change config
    #     self.is_P_priority = fleet_config.is_P_priority
    #     self.is_autonomous = fleet_config.is_autonomous
    #     self.FW_Param = fleet_config.FW_Param # FW_Param=[db_UF,db_OF,k_UF,k_OF]
    #     self.fw_function.db_UF = self.FW_Param[0]
    #     self.fw_function.db_OF = self.FW_Param[1]
    #     self.fw_function.k_UF = self.FW_Param[2]
    #     self.fw_function.k_OF = self.FW_Param[3]
    #     self.autonomous_threshold = fleet_config.autonomous_threshold
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
    '''
    Add necessary weather data by randomly sampling from a weather database for a summer cooling month;
    since we only stored one month data in 10 min resolution here, this code will automatically interpolate
    the data to desired resolution by ignoring the actual month in the 'time' format.
    '''
    #### Interpolate the time resolution of the disturbances
    def get_inputs(Qsolar_i10, Qsolar_mass10, temp_sol_W10, temp_sol_R10, timestep_s, ts):
        num_steps = 3600*24.0/timestep_s  
        dt = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        start_time_dec = dt.hour + dt.minute/60.0 + dt.seconds/3600.0

        new_time_list = np.linspace(start_time_dec, start_time_dec + timestep_s*num_steps/3600.0, num_steps)

        # Tout and IHG profiles preprocessed for 10 mins,
        # if other time step, better to do preprocess outside the main function here
        # or use timestep_min below (we set timestep_min = 10 by default)    
        # Qsolar_i10_file = np.matrix(Qsolar_i10)
        # Qsolar_mass10_file = np.matrix(Qsolar_mass10)
        # temp_sol_W10_file = np.matrix(temp_sol_W10)
        # temp_sol_R10_file = np.matrix(temp_sol_R10)    
        Qsolar_i = np.squeeze(np.asarray(Qsolar_i10))
        Qsolar_mass = np.squeeze(np.asarray(Qsolar_mass10))
        sol_W = np.squeeze(np.asarray(temp_sol_W10))
        sol_R = np.squeeze(np.asarray(temp_sol_R10))

        ## turn from 10 min original time resoution to any time resolution in seconds
        Qsolar_i_num_steps = Qsolar_i.shape[0]
        Qsolar_i_stepsize_min = 10
        Qsolar_i_orig_time = np.linspace(start_time_dec,
                                        start_time_dec + Qsolar_i_stepsize_min*Qsolar_i_num_steps/60.0,
                                        Qsolar_i_num_steps)       
        new_Qsolar_i = np.interp(new_time_list, Qsolar_i_orig_time, Qsolar_i)

        ## turn from 10 min original time resoution to any time resolution in seconds
        Qsolar_mass_num_steps = Qsolar_mass.shape[0]
        Qsolar_mass_stepsize_min = 10
        Qsolar_mass_orig_time = np.linspace(start_time_dec,
                                        start_time_dec + Qsolar_mass_stepsize_min*Qsolar_mass_num_steps/60.0,
                                        Qsolar_mass_num_steps)       
        new_Qsolar_mass = np.interp(new_time_list, Qsolar_mass_orig_time, Qsolar_mass)

        ## turn from 10 min original time resoution to any time resolution in seconds
        sol_W_num_steps = sol_W.shape[0]
        sol_W_stepsize_min = 10
        sol_W_orig_time = np.linspace(start_time_dec,
                                        start_time_dec + sol_W_stepsize_min*sol_W_num_steps/60.0,
                                        sol_W_num_steps)       
        new_sol_W = np.interp(new_time_list, sol_W_orig_time, sol_W)

        ## turn from 10 min original time resoution to any time resolution in seconds
        sol_R_num_steps = sol_R.shape[0]
        sol_R_stepsize_min = 10
        sol_R_orig_time = np.linspace(start_time_dec,
                                        start_time_dec + sol_R_stepsize_min*sol_R_num_steps/60.0,
                                        sol_R_num_steps)       
        new_sol_R = np.interp(new_time_list, sol_R_orig_time, sol_R)

        return new_Qsolar_i, new_Qsolar_mass, new_sol_W, new_sol_R

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

        num_steps = 3600*24.0/timestep_s   

        try:
            amb_temp_column = loc[climate_location]
            IHG_column = loc[climate_location]
        except IndexError:
            raise IndexError("Error! Only allowed installation locations for now !!!")

        dt = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        start_time_dec = dt.hour + dt.minute/60.0 + dt.seconds/3600.0

        new_time_list = np.linspace(start_time_dec, start_time_dec+timestep_s*num_steps/3600.0, num_steps)

        Tamb = []
        IHG = []

        # Tout and IHG profiles preprocessed for 10 mins,
        # if other time step, better to do preprocess outside the main function here
        # or use timestep_min below (we set timestep_min = 10 by default)
        ambient_cond_file = pd.read_excel('./data_file/Cities_Tout_July_10mins.xlsx') #load steply ambient air temperature file
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

        # turn from 10 min original time resoution to any time resolution in seconds
        IHG_file = pd.read_excel('./data_file/Cities_IHG_July_10mins.xlsx')  #load steply IHG file
        IHG_file = np.matrix(IHG_file)
        IHG = IHG_file[:,IHG_column]
        IHG = np.squeeze(np.asarray(IHG))

        IHG_num_steps = IHG.shape[0]
        IHG_stepsize_min = 10
        IHG_orig_time = np.linspace(start_time_dec,
                                    start_time_dec+IHG_stepsize_min*IHG_num_steps/60.0,
                                    IHG_num_steps)       
        new_IHG = np.interp(new_time_list, IHG_orig_time, IHG)

        return new_Tamb, new_IHG









