# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 15:07:49 2018
For GMLC 1.4.2, fleet Virtual Battery Model for HVACs
Based on a valided 4R4C building thermal model

Last update: 08/02/2018
Version: 1.0

@author: dongj@ornl.gov
"""

#from fleet_interface import FleetInterface
#from fleet_request   import FleetRequest
#from fleet_response  import FleetResponse


import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import random
import pandas as pd
import scipy as sp
import time

# this is the actual building thermal and HVAC models
#import build_model as bm
from build_model import BuildingModel
from build_model import AC

class HVACFleet():   #FleetInterface
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """
    def __init__(self, Steps = 100, Timestep = 10, P_request = 0, Q_request = 0, forecast = 0):
        """
        Constructor
        """
        
        # generate random houses based on the validated building model
        # varying R, C values by some coefficients
        # represents low efficiency, normal efficiency and high efficiency houses (corresponding to different envelope/insulation parameters)
        # for envelope type, location and max. number of service calls need to specify discrete values and randomly sampled to get a desired distribution 
        self.numHVAC = 200 #number of water heaters in fleet
#        Steps = 60 #num steps in simulation 6 steps = 1 hour 1 day = 24*6 = 144
#        lengthRegulation = 20 # num of 4-second steps for regulation signal
#        addshedTimestep = 10 # minutes, NOTE, MUST BE AN INTEGER DIVISOR OF 10. Acceptable numbers
        self.ts = 10  # mins/interval of discrete control
        
        self.MaxNumMonthlyConditions = 20 #max # of monthly conditions to calculate, if more HVACs than this just reuse some of the conditions and water draw profiles
        
        self.TinInitialMean = 23.67 #deg C
        self.TinInitialStddev = 0.3 #deg C
        
        self.TsetInitialMean = 23.0 #deg C  convert from 80F+-4
        self.TsetInitialStddev = 1   #2.22 #deg C
        
        self.minSOC = 0.2 # minimum SoC for aggregator to call for shed service
        self.maxSOC = 0.8 # minimum SoC for aggregator to call for add service
        
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
    
     
    
    def ExecuteFleet(self, Steps, Timestep, P_request, Q_request, forecast):
        
   
#    generate distribution of initial WH fleet states. this means Rext, Rattic, Cmass,
#    profile for the yr for each building in fleet, this will be imported later, just get something reasonable here
        TinInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        TwallInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        TmassInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        TatticInitial=np.random.normal(self.TinInitialMean, self.TinInitialStddev,self.numHVAC)
        
        TsetInitial=np.random.normal(self.TsetInitialMean, self.TsetInitialStddev,self.numHVAC)
        
        Rext = [random.choice(self.RextMasterList) for n in range(self.numHVAC)]
        Rattic = [random.choice(self.RatticMasterList) for n in range(self.numHVAC)]
        Cmass = [random.choice(self.CmassMasterList) for n in range(self.numHVAC)]
        Location = [random.choice(self.ClimateMasterList) for n in range(self.numHVAC)]
        
        MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numHVAC)]    
        
   ###########################################################################       
    #   for calculating monthly conditions
#        climate_location = 'Vegas' # only allowable climate for now 
    #    can be replaced by any weather profile which defines the outside disturbance
    #    V = [ Tsol_w,   QIHL_i,   Qsolar_i;   Tsol_r,   QIHL_mass,   Qsolar_mass]
 
        # load the weather profile
       
        measurement = pd.read_excel('./data_file/Vegas_TMY3_July_10mins.xlsx')   # or Min5_data_vegas.xlsx
#        measurement_or['Date/Time']=pd.to_datetime(measurement_or['Date/Time'])
#        measurement_or = measurement_or.set_index('Date/Time')
#        measurement = measurement_or.resample(str(ts)+'T').interpolate()  # interpolate from Hour to 10 min
        measurement = np.matrix(measurement)
        # Index of each outdoor disturbance in the imported file
        outdoor_temp_idx = 0
        rad_wall_idx = 8
        convect_heat_idx = 11
#        IHL_idx = 7
        rad_window_idx = 10
        rad_roof_idx = 9
        
        aw = 0.3
        ar = 0.8
        SHGC = 0.56
        Awin = 25.76  # window size m^2
        Sp1=0.93
        Sp2=0.10006
        Sp3=0.92997
    
        # Measurements

#        outdoor_temp = measurement[:, outdoor_temp_idx]
        rad_wall = measurement[:, rad_wall_idx]
        convect_heat = measurement[:, convect_heat_idx]
#        IHL = measurement.ix[:, IHL_idx]
        rad_window = measurement[:, rad_window_idx]
        rad_roof = measurement[:, rad_roof_idx]
    
        # Calculate T sol for walls
        temp_sol_W = 0.3*np.divide(rad_wall, convect_heat)       
    
        # Calculate T sol for attic
        temp_sol_R = 0.8*np.divide(rad_roof,convect_heat)
            
        # solar through windows
        Qsolar = np.multiply(np.multiply(rad_window, Awin), SHGC)
    
        # parameters in conversion    
            
        Qsolar_i = Sp3*Qsolar
        Qsolar_mass = (1-Sp3)*Qsolar    
    
        ############## Overall disturbance signal ###############
#        V = [Tsol_W, QIHL_i, Qsolar_i, Tsol_R, QIHL_mass, Qsolar_mass]
#       Tsol_W, QIHL_i, Tsol_RQ, and IHL_mass are radnomly generated based on the selected climate location!!!
         
        Tamb = []
        Tsol_W = []
        Tsol_R = []
        IHL = []

        for a in range(self.numHVAC):             
            if a <= (self.MaxNumMonthlyConditions-1): #if numHVAC > MaxNumAnnualConditions just start reusing older conditions to save computational time               
      
                (tamb, IHL_s) = get_monthly_conditions(Location[a])
                
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
        IHL_fleet_ave = IHL_fleet/self.numHVAC  # this averages all rows, where each row is a WH, so gives the fleet average of IHL at each step
 
        ##################################     
#    Initializing lists to be saved to track indivisual HVAC performance over each timestep
        
        Tset = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Tin = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Twall = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Tmass = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        Tattic = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        SoC = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        AvailableCapacityAdd = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        AvailableCapacityShed = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        ServiceCallsAccepted = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        ServiceProvided = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        IsAvailableAdd = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        IsAvailableShed = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        elementOn = [[0 for x in range(Steps)] for y in range(self.numHVAC)]
        TotalServiceProvidedPerHVAC = [0 for y in range(self.numHVAC)]
        TotalServiceProvidedPerTimeStep = [0 for y in range(Steps)]
        MaxServiceAddedPerTimeStep = [0 for y in range(Steps)]
        MaxServiceShedPerTimeStep = [0 for y in range(Steps)]
        TotalServiceCallsAcceptedPerHVAC = [0 for y in range(self.numHVAC)]    
   
        SoCInit = [0.5 for y in range(self.numHVAC)]
        AvailableCapacityAddInit = [0 for y in range(self.numHVAC)]
        AvailableCapacityShedInit = [0 for y in range(self.numHVAC)]
        IsAvailableAddInit = [1 for y in range(self.numHVAC)]
        IsAvailableShedInit = [1 for y in range(self.numHVAC)]
        
        P_req = 0
        ##############################################################################################################
 
    #    Initializing the building HVAC models
        hvacs = [BuildingModel(Tamb[0], Tsol_W[0], QIHL_i[0], Qsolar_i[0], Tsol_R[0],
                               QIHL_mass[0],Qsolar_mass[0], P_req, Rext[number], 
                               Rattic[number], Cmass[number], 0, MaxServiceCalls[number], self.ts) for number in range(self.numHVAC)]
        
        P_service = 0
        P_service_max = 0
        P_injected = 0
        P_injected_max = 0
        P_forecast = 0
        P_request_perHVAC = P_request[0] / self.numHVAC # this is only for the first step
#        print(P_request_perWH)
        
        Q_injected = 0
        Q_service = 0
        Q_service_max = 0
        Q_forecast = 0    
   
        # run through fleet once as a forecast just to get initial conditions
        number = 0
        for h in hvacs:
            fcst = 1   #  setting the forecast to 1 for this initialization only
            tin, twall, tmass, tattic, tset, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = h.execute(TinInitial[number], TwallInitial[number], TmassInitial[number], TatticInitial[number], TsetInitial[number], Tamb[number][0], Tsol_W[number][0], QIHL_i[number][0], Qsolar_i[0], Tsol_R[number][0], QIHL_mass[number][0], Qsolar_mass[0], Rext[number], Rattic[number], Cmass[number], P_request_perHVAC, ServiceCallsAccepted[number][0], elementOn[number][0], Timestep, IHL_fleet_ave[0], fcst) #forecast = 1
            number += 1
           
        for step in range(Steps):    
            number = 0
            servsum = 0
            servmax = 0
            servmax2 = 0
            NumDevicesToCall = 0
            laststep = step - 1
    
#            decision making about which HVAC to call on for service, check if available at last step, if so then 
#            check for SoC > self.minSOC and Soc < self.maxSOC

            if step == 0: #use the initialized values to determine how many devices are available
                for n in range(self.numHVAC):
                    if P_request_perHVAC > 0 and IsAvailableAddInit[n] > 0 and SoCInit[n] < self.maxSOC and AvailableCapacityAddInit[n] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perHVAC < 0 and IsAvailableShedInit[n] > 0 and SoCInit[n] > self.minSOC and AvailableCapacityShedInit[n] > self.minCapacityShed:
                        NumDevicesToCall += 1
            elif step > 0: #use the last temperature to determine how many devices are available
                for n in range(self.numHVAC):
                    if P_request_perHVAC > 0 and IsAvailableAdd[n][laststep] > 0 and SoC[n][laststep] < self.maxSOC and AvailableCapacityAdd[n][laststep] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perHVAC < 0 and IsAvailableShed[n][laststep] > 0 and SoC[n][laststep] > self.minSOC and AvailableCapacityShed[n][laststep] > self.minCapacityShed:
                        NumDevicesToCall += 1          
      
            P_request_perHVAC = P_request[step] / max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

            #################################
      
            for hvac in hvacs: #loop through all HVACs
                if step == 0:
                    ### call hvac.execute
                    tin, twall, tmass, tattic, tset, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = hvac.execute(TinInitial[number], TwallInitial[number], TmassInitial[number], TatticInitial[number],TsetInitial[number], Tamb[number][0], Tsol_W[number][0], QIHL_i[number][0], Qsolar_i[0], Tsol_R[number][0], QIHL_mass[number][0], Qsolar_mass[0], Rext[number], Rattic[number], Cmass[number],  0, ServiceCallsAccepted[number][0], elementOn[number][0], Timestep, IHL_fleet_ave[0], forecast)
                
                elif step>0 and P_request[step]>=0 and IsAvailableAdd[number][laststep] > 0 :
                # For step >=1, can use last step temperature...
                    TsetLast = Tset[number][laststep]
                    TinLast = Tin[number][laststep]     
                    TwallLast = Twall[number][laststep] 
                    TmassLast = Tmass[number][laststep] 
                    TatticLast = Tattic[number][laststep] 
             
                    tin, twall, tmass, tattic, tset, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = hvac.execute(TinLast, TwallLast, TmassLast, TatticLast, TsetLast, Tamb[number][step], Tsol_W[number][step], QIHL_i[number][step], Qsolar_i[step], Tsol_R[number][step], QIHL_mass[number][step], Qsolar_mass[step], Rext[number], Rattic[number], Cmass[number], P_request_perHVAC, ServiceCallsAccepted[number][laststep], elementOn[number][laststep], Timestep, IHL_fleet_ave[min([step,Steps-1])], forecast)

                    P_request[step] = P_request[step] - eservice*1e3


                elif step>0 and P_request[step]<0 and IsAvailableShed[number][laststep] > 0 :
                # For step >=1, can use last step temperature...
                    TsetLast = Tset[number][laststep]
                    TinLast = Tin[number][laststep]     
                    TwallLast = Twall[number][laststep] 
                    TmassLast = Tmass[number][laststep] 
                    TatticLast = Tattic[number][laststep] 
             
                    tin, twall, tmass, tattic, tset, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = hvac.execute(TinLast, TwallLast, TmassLast, TatticLast, TsetLast, Tamb[number][step], Tsol_W[number][step], QIHL_i[number][step], Qsolar_i[step], Tsol_R[number][step], QIHL_mass[number][step], Qsolar_mass[step], Rext[number], Rattic[number], Cmass[number], P_request_perHVAC, ServiceCallsAccepted[number][laststep], elementOn[number][laststep], Timestep, IHL_fleet_ave[min([step,Steps-1])], forecast)
                    P_request[step] = P_request[step] - eservice*1e3    
#                    break

                else:
                    TsetLast = Tset[number][laststep]
                    TinLast = Tin[number][laststep]     
                    TwallLast = Twall[number][laststep] 
                    TmassLast = Tmass[number][laststep] 
                    TatticLast = Tattic[number][laststep] 
             
                    tin, twall, tmass, tattic, tset, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = hvac.execute(TinLast, TwallLast, TmassLast, TatticLast, TsetLast, Tamb[number][step], Tsol_W[number][step], QIHL_i[number][step], Qsolar_i[step], Tsol_R[number][step], QIHL_mass[number][step], Qsolar_mass[step], Rext[number], Rattic[number], Cmass[number], 0, ServiceCallsAccepted[number][laststep], elementOn[number][laststep], Timestep, IHL_fleet_ave[min([step,Steps-1])], forecast)


#                assign returned parameters to associated lists to be recorded
                Tset[number][step] = tset
                Tin[number][step] = tin
                Twall[number][step] = twall
                Tmass[number][step] = tmass
                Tattic[number][step] = tattic
                
                SoC[number][step] = soC
                IsAvailableAdd[number][step] = isAvailableAdd
                IsAvailableShed[number][step] = isAvailableShed
                
                elementOn[number][step] = elementon
                AvailableCapacityAdd[number][step] = availableCapacityAdd
                AvailableCapacityShed[number][step] = availableCapacityShed
                ServiceCallsAccepted[number][step] = serviceCallsAccepted
                ServiceProvided[number][step] = eservice
                
                servsum += eservice*1e3
                TotalServiceProvidedPerHVAC[number] = TotalServiceProvidedPerHVAC[number] + ServiceProvided[number][step]
                P_injected += eused
                P_injected_max += pusedmax
                
                servmax += availableCapacityAdd*1e3
                servmax2 += availableCapacityShed*1e3
                
                number += 1  # go to next building

            TotalServiceProvidedPerTimeStep[step] = -1.0*servsum   # per time step for all hvacs
            MaxServiceAddedPerTimeStep[step] = servmax 
            MaxServiceShedPerTimeStep[step] = servmax2 
 
                    
        for n in range(number):
            TotalServiceCallsAcceptedPerHVAC[n] = ServiceCallsAccepted[n][step]
    
    
        for m in range(Steps):
            P_service += TotalServiceProvidedPerTimeStep[m]
            for q in range(number):
               P_service_max += AvailableCapacityShed[q][m] 
                
    
        if forecast == 1:
            P_forecast = P_service
        else:
            P_forecast = 0
    
        return TotalServiceProvidedPerTimeStep, MaxServiceAddedPerTimeStep, MaxServiceShedPerTimeStep, P_injected, Q_injected, P_service, Q_service, P_injected_max, Q_service_max, P_forecast, Q_forecast
   
###############################################################################    
# Add random climate zone during a summer cooling month
    
def get_monthly_conditions(climate_location):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        Tamb = []
        IHG = []

        # Orders of the locations:
        # Miami, Phon, Atl, Vegas, Den, Minnea
        
        if climate_location == 'Miami':            
            #raise NameError("Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
            amb_temp_column = 0
            IHG_column = 0
        elif climate_location == 'Phoenix':
            amb_temp_column = 1
            IHG_column = 1
        elif climate_location == 'Atlanta':
            amb_temp_column = 2
            IHG_column = 2
        elif climate_location == 'Las Vegas':
            amb_temp_column = 3
            IHG_column = 3
        elif climate_location == 'Denver':
            amb_temp_column = 4
            IHG_column = 4
        elif climate_location == 'Minneapolis':
            amb_temp_column = 5
            IHG_column = 5
        else:
            raise NameError("Error! Only allowed installation locations for now !!!")
 
        
        # Tout and IHG profiles preprocessed for 10 mins,
        # if other time step, better to do preprocess outside the main function here
        # or use timestep_min below (we set timestep_min = 10 by default)
        
   
        ambient_cond_file = pd.read_excel('./data_file/Cities_Tout_July_10mins.xlsx') #steply ambient air temperature and RH
        ambient_cond_file = np.matrix(ambient_cond_file)
        Tamb = ambient_cond_file[:,amb_temp_column]
        
   
        IHG_file = pd.read_excel('./data_file/Cities_IHG_July_10mins.xlsx')  #steply ambient air temperature and RH
        IHG_file = np.matrix(IHG_file)
        IHG = IHG_file[:,IHG_column]

        return Tamb, IHG


def change_config(self, **kwargs):
    """
    This function is here for future use. The idea of having it is for a service to communicate with a fleet
    in a nondeterministic manner during a simulation

    :param kwargs: a dictionary of (key, value) pairs. The exact keys are decided by a fleet.

    Example: Some fleets can operate in an autonomous mode, where they're not responding to requests,
    but watching, say, the voltage. If the voltage dips below some defined threshold (which a service might define),
    then the fleet responds in a pre-defined way.
    In this example, the kwargs can be {"voltage_threshold": new_value}
    """
    pass
    
if __name__ == '__main__':
    fleet = HVACFleet()
#    print(fleet.P_service)
#    print(fleet.P_forecast)






