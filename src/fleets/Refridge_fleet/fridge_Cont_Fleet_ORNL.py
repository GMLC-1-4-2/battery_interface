# -*- coding: utf-8 -*-
"""
Created on Mon June 2018
For GMLC 1.4.2, fleet Virtual Battery Model for Commercail Refridgeration Systems
Based on a valided 2R2C case thermal model

Last update: 08/06/2018
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
from case_model import CaseModel
from case_model import AC

class RFFleet():   #FleetInterface
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
        self.numRF = 50 #number of water heaters in fleet
#        Steps = 60 #num steps in simulation 6 steps = 1 hour 1 day = 24*6 = 144
#        lengthRegulation = 20 # num of 4-second steps for regulation signal
#        addshedTimestep = 10 # minutes, NOTE, MUST BE AN INTEGER DIVISOR OF 10. Acceptable numbers
        self.ts = 0.5  # mins/interval of discrete control
        
        self.MaxNumMonthlyConditions = 20 #max # of monthly conditions to calculate, if more HVACs than this just reuse some of the conditions and water draw profiles
        
        self.TairInitialMean = 7.22 #deg C
        self.TairInitialStddev = 0.5 #deg C
        
        self.TfoodInitialMean = 4.44 #deg C  convert from 80F+-4
        self.TfoodInitialStddev = 0.5   #2.22 #deg C
        
        self.minSOC = 0.02 # minimum SoC for aggregator to call for shed service
        self.maxSOC = 1.0 # minimum SoC for aggregator to call for add service
        
        self.minCapacityAdd = 150 #W-hr, minimum add capacity to be eligible for add service
        self.minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
     
        # Varying parameters for different Envelopes
        # R value of the exterior wall
        
        self.C_foodMasterList = [4633342, 4633342, 4633342, 4633342, 4633342, 3938340,  3938340, 
                  3938340, 5328343, 5328343]   # J/K 50% Normal, 30% Low-product, 20% High-product
        # R value of the attic
        self.R_caseMasterList = [0.09721, 0.09721, 0.09721, 0.09721, 0.082629, 0.082629, 
                    0.082629, 0.10693,  0.10693, 0.10693] # K/W 40% Normal, 30% Low-efficiency, 30% High-efficiency
        # C value of thermal mass
        self.R_foodMasterList = [0.001354, 0.001354, 0.001354, 0.001354, 0.001354,
                   0.001354, 0.001177, 0.001177, 0.001177, 0.001177]  # K/W 30% Normal, 60% Low-efficiency, 10% High-efficiency
        #  Typical US nationwide climate locations
        self.ClimateMasterList = ['Miami', 'Phoenix', 'Atlanta', 'Atlanta', 'Las Vegas', 'Denver',  
                             'Denver', 'Atlanta', 'Miami', 'Minneapolis'] # 20% Miami
        # 30% Atlanta; 20% Denver, 10% for Phoneix, Vegas and Minneapolis
        
        self.MaxServiceCallMasterList = [30, 20, 20, 10, 15, 25, 5, 15, 30] # this is the max number of monthly service calls for load add/shed.
        
         ########################################################################
    
     
    
    def ExecuteFleet(self, Steps, Timestep, P_request, Q_request, forecast):
        
   
#    generate distribution of initial WH fleet states. this means Rext, Rattic, Cmass,
#    profile for the yr for each building in fleet, this will be imported later, just get something reasonable here
        TairInitial=np.random.normal(self.TairInitialMean, self.TairInitialStddev,self.numRF)
        TfoodInitial=np.random.normal(self.TfoodInitialMean, self.TfoodInitialStddev,self.numRF)

        R_case = [random.choice(self.R_caseMasterList) for n in range(self.numRF)]
        R_food = [random.choice(self.R_foodMasterList) for n in range(self.numRF)]
        C_food = [random.choice(self.C_foodMasterList) for n in range(self.numRF)]
        Location = [random.choice(self.ClimateMasterList) for n in range(self.numRF)]
        
        MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numRF)]    
        
   ###########################################################################       
    #   for calculating monthly conditions
#        climate_location = 'Vegas' # only allowable climate for now 
    #    can be replaced by any weather profile which defines the outside disturbance
    #    V = [ Tsol_w,   QIHL_i,   Qsolar_i;   Tsol_r,   QIHL_mass,   Qsolar_mass]
 
        # load the weather profile
       

        # Index of each outdoor disturbance in the imported file
       
    
        ############## Overall disturbance signal ###############
#        V = [Tsol_W, QIHL_i, Qsolar_i, Tsol_R, QIHL_mass, Qsolar_mass]
#       Tsol_W, QIHL_i, Tsol_RQ, and IHL_mass are radnomly generated based on the selected climate location!!!
         
        oTamb = []
        oTind = []


        for a in range(self.numRF):             
            if a <= (self.MaxNumMonthlyConditions-1): #if numHVAC > MaxNumAnnualConditions just start reusing older conditions to save computational time               
      
                (tamb, Tind_s) = get_monthly_conditions(Location[a])
                

                oTamb.append(tamb)
                oTind.append(Tind_s)
 
            else: #start re-using conditions
                oTamb.append(oTamb[a - self.MaxNumMonthlyConditions][:])

                oTind.append(oTind[a - self.MaxNumMonthlyConditions][:])
        
    
        
        # Just take forecast of IHL as an example, it can be easily extended to solar irradiation
        Tind = np.asarray(oTind)
        
#        Mdot = np.clip(Mdot, 0, 1)
        Tind_fleet = sum(Tind)# this sums all rows, where each row is an refridge, so gives the fleet sum of IHL at each step
        Tind_ave = Tind_fleet/self.numRF  # this averages all rows, where each row is a refridge, so gives the fleet average of IHL at each step
        
        
        
        
        Tamb = np.asarray(oTamb)
#        Mdot = np.asarray(oMdot)
        Mdot_ave = np.asarray(Tind_ave)
        
        ##################################     
#    Initializing lists to be saved to track indivisual HVAC performance over each timestep
        

        Tair = [[0 for x in range(Steps)] for y in range(self.numRF)]
        Tfood = [[0 for x in range(Steps)] for y in range(self.numRF)]
        
        
        SoC = [[0 for x in range(Steps)] for y in range(self.numRF)]
        AvailableCapacityAdd = [[0 for x in range(Steps)] for y in range(self.numRF)]
        AvailableCapacityShed = [[0 for x in range(Steps)] for y in range(self.numRF)]
        ServiceCallsAccepted = [[0 for x in range(Steps)] for y in range(self.numRF)]
        ServiceProvided = [[0 for x in range(Steps)] for y in range(self.numRF)]
        IsAvailableAdd = [[0 for x in range(Steps)] for y in range(self.numRF)]
        IsAvailableShed = [[0 for x in range(Steps)] for y in range(self.numRF)]
        elementOn = [[0 for x in range(Steps)] for y in range(self.numRF)]
        TotalServiceProvidedPerHVAC = [0 for y in range(self.numRF)]
        TotalServiceProvidedPerTimeStep = [0 for y in range(Steps)]
        MaxServiceAddedPerTimeStep = [0 for y in range(Steps)]
        MaxServiceShedPerTimeStep = [0 for y in range(Steps)]
        TotalServiceCallsAcceptedPerHVAC = [0 for y in range(self.numRF)]    
   
        SoCInit = [0.5 for y in range(self.numRF)]
        AvailableCapacityAddInit = [0 for y in range(self.numRF)]
        AvailableCapacityShedInit = [0 for y in range(self.numRF)]
        IsAvailableAddInit = [1 for y in range(self.numRF)]
        IsAvailableShedInit = [1 for y in range(self.numRF)]
        
        P_req = 0
        ##############################################################################################################
 
    #    Initializing the building HVAC models
        RFs = [CaseModel(Tamb[0], Tind[0], P_req, R_case[number], R_food[number], C_food[number], 0, MaxServiceCalls[number], self.ts) for number in range(self.numRF)]
        
        P_service = 0
        P_service_max = 0
        P_injected = 0
        P_injected_max = 0
        P_forecast = 0
        P_request_perRF = P_request[0] / self.numRF # this is only for the first step
#        print(P_request_perWH)
        
        Q_injected = 0
        Q_service = 0
        Q_service_max = 0
        Q_forecast = 0    
   
        # run through fleet once as a forecast just to get initial conditions
        number = 0
        for h in RFs:
            fcst = 1   #  setting the forecast to 1 for this initialization only
            tair, tfood, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = h.execute(TairInitial[number], TfoodInitial[number], Tamb[number][0], Tind[number][0], R_case[number], R_food[number], C_food[number], P_request_perRF, ServiceCallsAccepted[number][0], elementOn[number][0], Timestep, Tind_ave[0], fcst) #forecast = 1
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
                for n in range(self.numRF):
                    if P_request_perRF > 0 and IsAvailableAddInit[n] > 0 and SoCInit[n] < self.maxSOC and AvailableCapacityAddInit[n] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perRF < 0 and IsAvailableShedInit[n] > 0 and SoCInit[n] > self.minSOC and AvailableCapacityShedInit[n] > self.minCapacityShed:
                        NumDevicesToCall += 1
            elif step > 0: #use the last temperature to determine how many devices are available
                for n in range(self.numRF):
                    if P_request_perRF > 0 and IsAvailableAdd[n][laststep] > 0 and SoC[n][laststep] < self.maxSOC and AvailableCapacityAdd[n][laststep] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perRF < 0 and IsAvailableShed[n][laststep] > 0 and SoC[n][laststep] > self.minSOC and AvailableCapacityShed[n][laststep] > self.minCapacityShed:
                        NumDevicesToCall += 1          
      
            P_request_perRF = P_request[step] / max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

            #################################
      
            for rfdg in RFs: #loop through all HVACs
                if step == 0:
                    ### call hvac.execute
                    tair, tfood, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = rfdg.execute(TairInitial[number], TfoodInitial[number], Tamb[number][0], Tind[number][0], R_case[number], R_food[number], C_food[number], P_request_perRF, ServiceCallsAccepted[number][0], elementOn[number][0], Timestep, Tind_ave[0],  forecast)
                
                elif step>0 and P_request[step] >= 0 and IsAvailableAdd[number][laststep] > 0:  # and IsAvailableAdd[number][laststep] > 0 
                # For step >=1, can use last step temperature...
                    TairLast = Tair[number][laststep]     
                    TfoodLast = Tfood[number][laststep] 
             
                    tair, tfood, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = rfdg.execute(TairLast, TfoodLast, Tamb[number][step], Tind[number][step],  R_case[number], R_food[number], C_food[number], P_request_perRF, ServiceCallsAccepted[number][laststep], elementOn[number][laststep], Timestep, Tind_ave[min([step,Steps-1])], forecast)

                    P_request[step] = P_request[step] - eservice*1

                elif step>0 and P_request[step]<0 and IsAvailableShed[number][laststep] > 0 :  # 
                # For step >=1, can use last step temperature...
                    TairLast = Tair[number][laststep]     
                    TfoodLast = Tfood[number][laststep] 
             
                    tair, tfood, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = rfdg.execute(TairLast, TfoodLast, Tamb[number][step], Tind[number][step],  R_case[number], R_food[number], C_food[number], P_request_perRF, ServiceCallsAccepted[number][laststep], elementOn[number][laststep], Timestep, Tind_ave[min([step,Steps-1])], forecast)
                    P_request[step] = P_request[step] - eservice*1
#                    

                else:   # no service
#                    TsetLast = Tset[number][laststep]
                    TairLast = Tair[number][laststep]     
                    TfoodLast = Tfood[number][laststep] 
 
                    tair, tfood, eused, pusedmax, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed = rfdg.execute(TairLast, TfoodLast, Tamb[number][step], Tind[number][step], R_case[number], R_food[number], C_food[number], 0, ServiceCallsAccepted[number][laststep], elementOn[number][laststep], Timestep, Tind_ave[min([step,Steps-1])], forecast)
#                    eservice = 0

#                assign returned parameters to associated lists to be recorded
  
                Tair[number][step] = tair
                Tfood[number][step] = tfood 
                
                SoC[number][step] = soC
                IsAvailableAdd[number][step] = isAvailableAdd
                IsAvailableShed[number][step] = isAvailableShed
                
                elementOn[number][step] = elementon
                AvailableCapacityAdd[number][step] = availableCapacityAdd
                AvailableCapacityShed[number][step] = availableCapacityShed
                ServiceCallsAccepted[number][step] = serviceCallsAccepted
                
                ServiceProvided[number][step] = eservice
                
                servsum += eservice*1
                TotalServiceProvidedPerHVAC[number] = TotalServiceProvidedPerHVAC[number] + ServiceProvided[number][step]
                P_injected += eused
                P_injected_max += pusedmax
                
                servmax += availableCapacityAdd*1
                servmax2 += availableCapacityShed*1
                
                number += 1  # go to next building

            TotalServiceProvidedPerTimeStep[step] = 1.0*servsum # if P_request[step] > 0 >0 else -1.0*servsum   # per time step for all hvacs
            MaxServiceAddedPerTimeStep[step] = servmax 
            MaxServiceShedPerTimeStep[step] = servmax2 
 
                    
        for n in range(number):
            TotalServiceCallsAcceptedPerHVAC[n] = ServiceCallsAccepted[n][step]
    
    
        for m in range(Steps):
            P_service += TotalServiceProvidedPerTimeStep[m] * 1
            for q in range(number):
               P_service_max += AvailableCapacityShed[q][m] * 1e3
                
    
        if forecast == 1:
            P_forecast = P_service
        else:
            P_forecast = 0
    
        return TotalServiceProvidedPerTimeStep, MaxServiceAddedPerTimeStep, MaxServiceShedPerTimeStep, P_injected, Q_injected, P_service, Q_service, P_service_max, Q_service_max, P_forecast, Q_forecast
   
###############################################################################    
# Add random climate zone during a summer cooling month
    
def get_monthly_conditions(climate_location):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        Tamb = []
        Mdot = []
#        IHG = []

        # Orders of the locations:
        # Miami, Phon, Atl, Vegas, Den, Minnea
        
        if climate_location == 'Miami':            
            #raise NameError("Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
            amb_temp_column = 0
#            IHG_column = 0
        elif climate_location == 'Phoenix':
            amb_temp_column = 1
#            IHG_column = 1
        elif climate_location == 'Atlanta':
            amb_temp_column = 2
#            IHG_column = 2
        elif climate_location == 'Las Vegas':
            amb_temp_column = 3
#            IHG_column = 3
        elif climate_location == 'Denver':
            amb_temp_column = 4
#            IHG_column = 4
        elif climate_location == 'Minneapolis':
            amb_temp_column = 5
#            IHG_column = 5
        else:
            raise NameError("Error! Only allowed installation locations for now !!!")
 
        
        # Tout and IHG profiles preprocessed for 10 mins,
        # if other time step, better to do preprocess outside the main function here
        # or use timestep_min below (we set timestep_min = 10 by default)
        
   
        ambient_cond_file = pd.read_excel('./data_file/Cities_Tout_July_10mins.xlsx') #steply ambient air temperature and RH
        ambient_cond_file = np.matrix(ambient_cond_file)
        Tamb = ambient_cond_file[:,amb_temp_column]
        
      
        
        Tin_file = pd.read_excel('./data_file/Tindoor.xlsx')  #steply ambient air temperature and RH
        Tin_filer = np.matrix(Tin_file)
        Tin_filer2 = Tin_filer[0:len(Tamb)-1]
        Tind = (Tin_filer2[:]-32)/1.8  #np.max(Mdot_filer2)

        return Tamb,  Tind


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
    fleet = RFFleet()
#    print(fleet.P_service)
#    print(fleet.P_forecast)






