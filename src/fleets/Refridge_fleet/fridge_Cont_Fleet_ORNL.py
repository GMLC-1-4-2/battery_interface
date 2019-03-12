# -*- coding: utf-8 -*-
"""
Created on Mon June 2018
For GMLC 1.4.2, fleet Virtual Battery Model for Commercail Refridgeration Systems
Based on a valided 2R2C case thermal model

Last update: 02/14/2019
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

# this is the actual Refridges models
from case_model import CaseModel
from case_model import AC

#from fleet_response import FleetResponse   #Commercial Fridge Fleet
from fleet_response import FleetResponse
from fleet_interface import FleetInterface

class RFFleet():   #FleetInterface
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """
    def __init__(self, Steps = 100, Timestep = 10, P_request = 0, Q_request = 0, forecast = 0, StartHr = 40):
        """
        Constructor
        """

        # generate random houses based on the validated building model
        # varying R, C values by some coefficients
        # represents low efficiency, normal efficiency and high efficiency houses (corresponding to different envelope/insulation parameters)
        # for envelope type, location and max. number of service calls need to specify discrete values and randomly sampled to get a desired distribution
        self.numRF = 50 #number of commercial refrigeration systems in fleet
#        Steps = 60 #num steps in simulation 6 steps = 1 hour 1 day = 24*6 = 144
#        lengthRegulation = 20 # num of 4-second steps for regulation signal
#        addshedTimestep = 10 # minutes, NOTE, MUST BE AN INTEGER DIVISOR OF 10. Acceptable numbers
        self.ts = 0.5  # mins/interval of discrete control

        self.MaxNumMonthlyConditions = 20 #max # of monthly conditions to calculate, if more Refridges than this just reuse some of the conditions and water draw profiles

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

    def process_request(self, ServiceRequest):
        
        response = self.ExecuteFleet(ServiceRequest)   #response        
        return response     

    def forecast(self, fleet_requests):
        responses = []
        for request in fleet_requests:
            response = self.ExecuteFleet(request, forecast=1)
            responses.append(response)

        return responses
    
    def ExecuteFleet(self, ServiceRequest):

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
            if a <= (self.MaxNumMonthlyConditions-1): #if numRefridges > MaxNumAnnualConditions just start reusing older conditions to save computational time

                (tamb, Tind_s) = get_monthly_conditions(Location[a], ServiceRequest.Timestep, ServiceRequest.Steps, ServiceRequest.StartTime)
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
#    Initializing lists to be saved to track indivisual refridgeration performance over each timestep

        Tair = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        Tfood = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]

        SoC = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        
        AvailableCapacityAdd = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        AvailableCapacityShed = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        ServiceCallsAccepted = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        ServiceProvided = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        IsAvailableAdd = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        IsAvailableShed = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        elementOn = [[0 for x in range(ServiceRequest.Steps)] for y in range(self.numRF)]
        
        TotalServiceProvidedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]
        MaxServiceAddedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]


        SoCInit = [0.5 for y in range(self.numRF)]
        AvailableCapacityAddInit = [0 for y in range(self.numRF)]
        AvailableCapacityShedInit = [0 for y in range(self.numRF)]
        IsAvailableAddInit = [1 for y in range(self.numRF)]
        IsAvailableShedInit = [1 for y in range(self.numRF)]

        ServiceRequest.P_req = 0
        ##############################################################################################################

    #    Initializing the refridgeration models
        RFs = [CaseModel(Tamb[0], Tind[0], ServiceRequest.P_req, R_case[number], R_food[number], C_food[number], 0, MaxServiceCalls[number], self.ts) for number in range(self.numRF)]

        FleetResponse.P_service = 0
        FleetResponse.P_service_max = 0
        FleetResponse.P_togrid = 0
        FleetResponse.P_togrid_max = 0
        FleetResponse.P_togrid_min = 0
        FleetResponse.P_forecast = 0
        FleetResponse.E = 0
        FleetResponse.C = 0     
        
        P_request_perRF = ServiceRequest.P_request[0] / self.numRF # this is only for the first step
#        print(P_request_perWH)

        FleetResponse.Q_togrid = 0
        FleetResponse.Q_service = 0
        FleetResponse.Q_service_max = 0
        FleetResponse.Q_service_min = 0
        FleetResponse.Q_togrid_min = 0  
        FleetResponse.Q_togrid_max = 0  
        Eloss = 0
        Edel = 0 

        # run through fleet once as a forecast just to get initial conditions
        number = 0
        for h in RFs:
            fcst = 1   #  setting the forecast to 1 for this initialization only
            response = h.execute(TairInitial[number], TfoodInitial[number], Tamb[number][0], Tind[number][0], R_case[number], R_food[number], C_food[number], P_request_perRF, ServiceRequest.Timestep, Tind_ave[0], fcst) #forecast = 1
            number += 1

        for step in range(ServiceRequest.Steps):
            number = 0
            servsum = 0
            servmax = 0
            servmax2 = 0
            NumDevicesToCall = 0
            laststep = step - 1
#            decision making about which refridgeration to call on for service, check if available at last step, if so then
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

            P_request_perRF = ServiceRequest.P_request[step] / max(NumDevicesToCall,1) #divide the fleet request by the number of devices that can be called upon

            #################################

            for rfdg in RFs: #loop through all Refridges
                if step == 0:
                    ### call rfdg.execute
                    response = rfdg.execute(TairInitial[number], TfoodInitial[number], Tamb[number][0], Tind[number][0], R_case[number], R_food[number], C_food[number], P_request_perRF,  ServiceRequest.Timestep, Tind_ave[0],  ServiceRequest.Forecast)

                elif step>0 and ServiceRequest.P_request[step] <= 0 and IsAvailableAdd[number][laststep] > 0:  # and IsAvailableAdd[number][laststep] > 0
                # For step >=1, can use last step temperature...
                    TairLast = Tair[number][laststep]
                    TfoodLast = Tfood[number][laststep]

                    response = rfdg.execute(TairLast, TfoodLast, Tamb[number][step], Tind[number][step],  R_case[number], R_food[number], C_food[number], P_request_perRF, ServiceRequest.Timestep, Tind_ave[min([step,ServiceRequest.Steps-1])], ServiceRequest.Forecast)

                    ServiceRequest.P_request[step] = ServiceRequest.P_request[step] - response.Eservice

                elif step>0 and ServiceRequest.P_request[step]>0 and IsAvailableShed[number][laststep] > 0 :  #
                # For step >=1, can use last step temperature...
                    TairLast = Tair[number][laststep]
                    TfoodLast = Tfood[number][laststep]

                    response = rfdg.execute(TairLast, TfoodLast, Tamb[number][step], Tind[number][step],  R_case[number], R_food[number], C_food[number], P_request_perRF,  ServiceRequest.Timestep, Tind_ave[min([step,ServiceRequest.Steps-1])], ServiceRequest.Forecast)
                    ServiceRequest.P_request[step] = ServiceRequest.P_request[step] - response.Eservice
#

                else:   # no service
#                    TsetLast = Tset[number][laststep]
                    TairLast = Tair[number][laststep]
                    TfoodLast = Tfood[number][laststep]

                    response = rfdg.execute(TairLast, TfoodLast, Tamb[number][step], Tind[number][step], R_case[number], R_food[number], C_food[number], 0, ServiceRequest.Timestep, Tind_ave[min([step,ServiceRequest.Steps-1])], ServiceRequest.Forecast)
#                    eservice = 0

#                assign returned parameters to associated lists to be recorded

                Tair[number][step] = response.Tair
                Tfood[number][step] = response.Tfood

                SoC[number][step] = response.SOC
                IsAvailableAdd[number][step] = response.IsAvailableAdd
                IsAvailableShed[number][step] = response.IsAvailableShed

                elementOn[number][step] = response.ElementOn
                AvailableCapacityAdd[number][step] = response.AvailableCapacityAdd
                AvailableCapacityShed[number][step] = response.AvailableCapacityShed
                ServiceCallsAccepted[number][step] = response.ServiceCallsAccepted

                ServiceProvided[number][step] += response.Eservice

                servsum += response.Eservice*1
                
                
                FleetResponse.P_togrid += response.Eused
                FleetResponse.P_togrid_max += response.PusedMax
                FleetResponse.P_togrid_min += response.PusedMin
                FleetResponse.P_service += response.Eservice

                number += 1  # go to next building
                
                FleetResponse.E = 0
                FleetResponse.C += response.SOC / (self.numRF)
                FleetResponse.P_service_max += response.AvailableCapacityShed # NOTE THIS ASSUMES THE MAX SERVICE IS LOAD SHED
                
            FleetResponse.P_dot_up = FleetResponse.P_togrid_max / ServiceRequest.Timestep.seconds
            FleetResponse.P_dot_down = FleetResponse.P_togrid / ServiceRequest.Timestep.seconds
            FleetResponse.P_service_min  = 0
            FleetResponse.Q_dot_up       = 0
            FleetResponse.Q_dot_down     = 0
            FleetResponse.dT_hold_limit  = None
            FleetResponse.T_restore      = None
            FleetResponse.Strike_price   = None
            FleetResponse.SOC_cost       = None

            TotalServiceProvidedPerTimeStep[step] = -1.0*servsum   # per time step for all Refridges            


        if ServiceRequest.Forecast == 1:
            FleetResponse.P_forecast = FleetResponse.P_service
        else:
            FleetResponse.P_forecast = 0
    
        # return TotalServiceProvidedPerTimeStep, MaxServiceAddedPerTimeStep, MaxServiceShedPerTimeStep, P_injected, Q_injected, P_service, Q_service, P_injected_max, Q_service_max, P_forecast, Q_forecast
        return FleetResponse

###############################################################################
# Add random climate zone during a summer cooling month

loc = dict()
loc["Miami"] = 0
loc["Phoenix"] = 1
loc["Atlanta"] = 2
loc["Las Vegas"] = 3
loc["Denver"] = 4
loc["Minneapolis"] = 5

def get_monthly_conditions(climate_location,  timestep_min, num_steps, start_time):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        try:
            amb_temp_column = loc[climate_location]
            IHG_column = loc[climate_location]
        except IndexError:
            raise IndexError("Error! Only allowed installation locations for now !!!")

        dt = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        start_time_dec = dt.hour+dt.minute/60.0

        new_time_list = np.linspace(start_time_dec, start_time_dec+timestep_min*num_steps/60.0, num_steps)

        Tamb = []
        Tind = []
   
        # Tout and IHG profiles preprocessed for 10 mins,
        # if other time step, better to do preprocess outside the main function here
        # or use timestep_min below (we set timestep_min = 10 by default)
        ambient_cond_file = pd.read_excel('./data_file/Cities_Tout_July_10mins.xlsx') #steply ambient air temperature
        ambient_cond_file = np.matrix(ambient_cond_file)
        Tamb = ambient_cond_file[:,amb_temp_column]
        Tamb = np.squeeze(np.asarray(Tamb))

        Tamb_num_steps = Tamb.shape[0]
        Tamb_stepsize_min = 10
        Tamb_orig_time = np.linspace(start_time_dec,
                                     start_time_dec+Tamb_stepsize_min*Tamb_num_steps/60.0,
                                     Tamb_num_steps)       
        new_Tamb = np.interp(new_time_list, Tamb_orig_time, Tamb)



        Tin_file = pd.read_excel('./data_file/Tindoor.xlsx')  #steply indoor temperature
        Tin_file = np.matrix(Tin_file)
        Tind = np.squeeze(Tin_file)


        Tind_num_steps = Tind.shape[0]
        Tind_stepsize_min = 10
        Tind_orig_time = np.linspace(start_time_dec,
                                     start_time_dec+Tind_stepsize_min*Tind_num_steps/60.0,
                                     Tind_num_steps)       
        n_Tind = np.interp(new_time_list, Tind_orig_time, Tind)




        new_Tind = (n_Tind[:]-32)/1.8  #np.max(Mdot_filer2) to get degree C

        return new_Tamb,  new_Tind


#def change_config(self, **kwargs):
#    """
#    This function is here for future use. The idea of having it is for a service to communicate with a fleet
#    in a nondeterministic manner during a simulation
#
#    :param kwargs: a dictionary of (key, value) pairs. The exact keys are decided by a fleet.
#
#    Example: Some fleets can operate in an autonomous mode, where they're not responding to requests,
#    but watching, say, the voltage. If the voltage dips below some defined threshold (which a service might define),
#    then the fleet responds in a pre-defined way.
#    In this example, the kwargs can be {"voltage_threshold": new_value}
#    """
#    pass
#
#if __name__ == '__main__':
#    fleet = RFFleet()
##    print(fleet.P_service)
##    print(fleet.P_forecast)
