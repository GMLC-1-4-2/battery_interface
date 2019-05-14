# -*- coding: utf-8 -*-
"""
Created on June 2018
For GMLC 1.4.2, generate the desired case thermal model 
High level 2R2C model

Last update: 02/14/2019
Version: 1.0

States 
X = [Tcase  Tfood]'

Control 
u = [Qac_i]



If defrost considered, every 4 hours, turn off refrigeration part for 50 min
For defrost in MT case, no electrical heating is needed, only need to keep the fan on 400 W.    

@author: Jin Dong, Borui Cui, Jian Sun, Jeffrey Munk, Teja Kuruganti

ORNL
"""

# depending on the IDE used these libraries might need to be imported manually

import numpy as np
#import control
import pandas as pd

#########################################################################


#Case characteristics    

class CaseModel():
    def __init__(self, Tamb = 25.0, Tset = 6, R_case=0.044077, R_food=0.004614, R_infil=0.008341, C_case=10200510, C_food=2844769, 
                    C_air=111053.5, time_step = 10, 
                    Element_onB = 0, Element_on = 0, lockonB = 0, lockoffB = 0,  lockon = 0, lockoff = 0, cycle_off_base = 0, 
                    cycle_on_base = 0, cycle_off_grid = 0, cycle_on_grid = 0):
        # RF Characteristic Information           

        # , cycle_defrost = 0

        
        self.Rcase=0.044077
        self.Rfood=0.004614
        self.Rinfil=0.008341

        self.Ccase=10200510       
        self.Cfood=2844769
        self.Cair=111053.5

        self.C1=0.296941      

        # Splitting coefficients for RF cooling
        self.Sp1=0.316882
        
        self.dt = [time_step*1.0]   # in seconds discretization

        self.Twall = [23.33]
        self.Tin = [23.0]
        self.Tattic = [23.8]
        self.Tim = [23.5]

        
#        C_Product = 4633342 #J/K
#        
#        R_Case = 0.097211  #K/W
#        R_food = 0.001177  #K/W
        
#        def __init__(self, Qrated, EIRrated):
#            self.Qrated=Qrated
#            self.EIRrated=EIRrated
#
#AC = AC(1.15,0.85)  

#def model(z,t,*u):
#    Rcase,Rfood,Cair,Cfood,Qheat,Tamb,Tevap,Qsens,infil,C1 = u
#    x1=z[0]
#    x2=z[1]
#    m_dot_Cair=455.7897
#    dx1dt=((Tamb-x1)/Rcase+(x2-x1)/Rfood-C1*Qsens+Qheat+(Tamb-x1)*m_dot_Cair*infil)/Cair
#    dx2dt=((x1-x2)/Rfood)/Cfood
#    dzdt=[dx1dt,dx2dt]
#    return dzdt

# Curve generated from Brian's report for R-404A       
def Capacity(Tout):
    return(1.0*(-200.8032*Tout + 36132.5296))  # tout in C,  Capacity in Btu/h 32 000 convert to 9.38 kw
    
    # def execute(self, Tair, Tfood, Tcase, Tset, Tamb, R_case, R_food, R_infil, C_case, C_food, C_air, control_signal, timestep, Element_on, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid):
        # # (Tin, Twall, Tmass, Tattic, Tset, Eused, PusedMax, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available_add, is_available_shed) = self.HVAC(Tin, Twall, Tmass,  Tattic, Tset, Tamb, Tsol_w, QIHL_i, Qsolar_i, Tsol_r, QIHL_mass, Qsolar_mass, Rwall, Rattic, Cmass, control_signal, 
        # #      service_calls_accepted, Element_on, self.max_service_calls, timestep, forecast_IHL, IsForecast)
        # (response) = self.FRIDGE(Tair, Tfood, Tcase, Tset, Tamb, R_case, R_food, R_infil, C_case, C_food, C_air, control_signal, 
                # timestep, Element_on, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid)
        
        # return response


        # , cycle_defrost


    def FRIDGE(self, Tair_lastB, Tfood_lastB, Tcase_lastB, Tair_last, Tfood_last, Tcase_last, Tset, Tamb_ts, R_case, R_food, R_infil, C_case, C_food, C_air, control_signal_ts, 
                timestep, Element_on_tsB, Element_on_ts, lockonB, lockoffB, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid):

        #############################################################################
                #        Baseline operation - Base Loads
        #############################################################################
        CM = CaseModel
        ts = timestep
        # ts = 10

        shortcycle_ts = int(round(shortcycle/ts,0))  #number of time steps during short cycle timer
        minrun_ts = int(round(minrun/ts,0))
            
        # estimate on what the maximum power usage could be
        E_cool= 1e-3*WMT(AC_RF, Tamb_ts)     # power consumpstion in kW
        Eused_baseline_ts = 0

        E_fan = 0.4                          # fan power consumption during defrost
        # PusedMax_ts = 1e-3*Capacity(AC,Tamb_ts)*EIR(AC,Tamb_ts)   # max instant power (EIR or COP is changing)         
        # Element_on_ts = 0        

        # Record control states  
        # if cycle_defrost >= 50*60:
        #     Element_on_tsB == 0 
        #     Eused_baseline_ts = E_fan
        #     lockoffB += 1*ts
        #     cycle_defrost += 1*ts
        #     cycle_defrost_off 
        # else:            
        # switch on
        if Tair_lastB > Tset + self.Tdeadband and lockoffB >= 2*60.0 and Element_on_tsB == 0 :  # and Element_on_tsB == 0 

            Element_on_tsB = 1
            Eused_baseline_ts = E_cool*1.000 # kW used
            cycle_on_base += 1 #count cycles turning from off to on
            # lockonB = 1*ts # start recording on period
            lockoffB += 1*ts

        # switch off

        elif Tair_lastB <= (Tset - self.Tdeadband) and Element_on_tsB == 1 :

            Eused_baseline_tsB = 0 # kW used
            Element_on_tsB = 0
            cycle_off_base += 1  # count cycles  turning from ON to OFF
            lockoffB = 1*ts # start recording off period
            # lockonB = 0

        else:
            Eused_baseline_ts = Element_on_tsB * E_cool
            lockoffB += 1*ts
        
            # if Element_on_ts:
                # lockonB += 1*ts
            # else:
                # lockoffB += 1*ts # cumulating recording off period         
        
        # # Record baseline states                    
        # Evolution of 3 states

        dTair_baseline=((Tamb_ts - Tair_lastB)/R_infil + (Tfood_lastB-Tair_lastB)/R_food + (Tcase_lastB-Tair_lastB)/R_case - Element_on_tsB*self.C1*QMT(AC_RF, Tamb_ts)*self.Sp1)/C_air/ts #x1 is Tair
        dTfood_baseline=((Tair_lastB - Tfood_lastB)/R_food)/C_food/ts #x2 is Tfood
        dTcase_baseline=((Tair_lastB - Tcase_lastB)/R_case - Element_on_tsB*self.C1*QMT(AC_RF, Tamb_ts)*(1-self.Sp1))/C_case/ts                
                        
        Tair_bas = Tair_lastB + dTair_baseline 
        Tfood_bas = Tfood_lastB + dTfood_baseline
        Tcase_bas = Tcase_lastB + dTcase_baseline  

        Element_on_bas = Element_on_tsB
                                
#            dT_power_input = Eused_ts*timestep*60/(3.79*self.Capacity*4810) #timestep is in minutes so mult by 60 to get seconds


class CaseModel():
        def __init__(self, Tamb = 25.0, Tind = 22, control_signal = 'none', R_Case = 0.097211, 
                     R_food = 0.001177, C_food = 4633342, service_calls_accepted = 0, max_service_calls = 20, time_step = 0.5, forecast_IHL = 0):
            # Building Thermal Characteristic Information
            
            
            # These three as input variables dependant on Envelope types
#            self.Rwall=.00852  # without multiplier is CC1
#            self.Rattic=.03441 # without multiplier is CC1
#            self.Cmass=29999128.0
            
            self.Cair = 1793.031*3   # J/K
#            self.C_food = 4633342 #J/K
#            
#            self.R_Case = 0.097211  #K/W
#            self.R_food = 0.001177 #K/W
                       
            self.Qsens = [0]
            self.m_dot = [100]
            self.infil = [0.6]
            
            self.C1 = 0.5
            self.Qheat = [800.0]
            
            self.dt = [time_step*60.0]   # 10 mins discretization

            self.Tair = [2]
            self.Tfood = [3.2]
      
            self.Tambient = [25.0]
          
            self.max_service_calls = int(max_service_calls)
            
            self.T_food_set = 3.5
            self.T_air_set = 2
            
            self.Tdeadband = 0.5
            
            self.T_food_min = (33.8-32)/1.8 # deg 1 C    regular food is [2, 5]
            self.T_food_max = (47.5-32)/1.8 # deg 7.5 C
            
            self.T_air_min = (32.36 - 32)/1.8 # deg 0.2 C  regular range is [1.5, 2.5]
            self.T_air_max = (42.2 - 32)/1.8 # deg 4 C
            
 #############################################################################
# Validated 2-story single family house model CC1
# state-space model to check the controllability and simplify the design of MPC (in the future)           
            CM = CaseModel
            
  #############################################################################
        def Capacity(Tout):
            return(1.0*(-200.8032*Tout + 36132.5296))  # tout in C,  Capacity in Btu/h 32 000 convert to 9.38 kw  9.38/32000.0
    
        def COP(Tout):
            return(-0.04418*Tout + 3.5892)   #Tout in C      1.8 ~ 2.9   
            
            
        def execute(self, Tair, Tfood, Tamb, Tind, R_case, R_food, C_food, control_signal, timestep, forecast_Tind, IsForecast):
            (response) = self.FRIDGE(Tair, Tfood, Tamb, Tind, R_case, R_food, C_food, control_signal, 
                 timestep, forecast_Tind, IsForecast)
            
            return response #Tair, Tfood, Eused, PusedMax, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available_add, is_available_shed, 
    
        def FRIDGE(self, Tair_last, Tfood_last, Tamb_ts, Tind_ts, R_case, R_food, C_food, control_signal_ts, 
                 timestep, forecast_Tind, is_forecast):
        
        
#############################################################################
        #        Baseline operation - Base Loads
#############################################################################
#            BM = BuildingModel
#            ts = timestep
            ts = 10
                
          #estimate on what the maximum power usage could be
            E_cool= 1.000*Capacity(Tamb_ts)/COP(Tamb_ts)     # power consumpstion in W
            Eused_baseline_ts = 0
            PusedMax_ts = Capacity(Tamb_ts)/COP(Tamb_ts)   # max instant power (EIR or COP is changing)
 
            Element_on_ts = 0

            service_calls_accepted_ts += 1
            cycle_off_grid += 1
            lockoff = 1*ts # start recording on period

        # elif control_signal_ts  > 0 and Tair_last >= Tset + self.Tdeadband:
            # # don't change anything
            # Eused_ts = Eused_baseline_ts
            
        # # Increase loads    

   
        elif control_signal_ts  < 0 and Tair_last >= (Tset - self.Tdeadband) and Element_on_tsB == 0 and lockoff >= 2*60.0: #Element_on_ts = 0 requirement eliminates free rider situation  

            #make sure it stays on
            Eused_ts = E_cool*1.000 #W used
            Element_on_ts = 1
            service_calls_accepted_ts += 1
            cycle_on_grid += 1
            lockoff += 1*ts # start recording on period

        else:#no changes
            Eused_ts = Eused_baseline_ts
            lockoff += 1*ts # cumulating recording off period 
        
        #calculate energy provided as a service, >0 is load add, <0 load shed
        # if the magnitude of the service that could be provided is greater than what is requested, just use what is requested and adjust the element on time
#        print('Available',abs(Eused_ts-Eused_baseline_ts), 'requested',control_signal_ts[1])

#            if abs(Eused_ts-Eused_baseline_ts) > abs(control_signal_ts): 
#                Eservice_ts = control_signal_ts
#                Eused_ts = control_signal_ts + Eused_baseline_ts
#                Element_on_ts = control_signal_ts/(Eused_ts-Eused_baseline_ts)
#            else: # assumes HVAC can't meet the entire request so it just does as much as it can
#                Eservice_ts = Eused_ts-Eused_baseline_ts
    
            Eservice_ts = Eused_ts - Eused_baseline_ts
                
#            print('Tfood:')    
#            print(Tfood_last)
#            print('Tair:')    
#            print(Tair_last)
#            print('Tind:')    
#            print(Tind_ts)
#            print('Predict Tind')
#            print(forecast_Tind)
#            print(self.Qheat*Mdot_fcst)
            
            dTair = 1.0/AC.C_Air * ((Tind_ts - Tair_last)/R_case + (Tfood_last-Tair_last)/R_food - self.C1 * Element_on_ts*Capacity(Tamb_ts) + 1 * self.Qheat + (Tind_ts-Tair_last)*AC.m_dot_Cair * self.infil)   #*Mdot_ts
            
            dTfood = 1.0/C_food * ((Tair_last - Tfood_last)/R_food)   #*(1-self.Sp3)
          
            Tair_ts = Tair_last + dTair 
            Tfood_ts = Tfood_last + dTfood

            
#            dT_power_input = Eused_ts*timestep*60/(3.79*self.Capacity*4810) #timestep is in minutes so mult by 60 to get seconds

    #        Calculate more parameters to be passed up
    #       update SoC
            SOC = (self.T_air_max - Tair_ts)/(self.T_air_max - self.T_air_min)
     
#            isAvailable_add_ts = 1 if max_service_calls > service_calls_accepted_ts  else 0
######################################################################################        
        #simple method to forecast availability for providing a service during next timestep
#        isAvailable_ts = 1 if max_service_calls > service_calls_accepted_ts  else 0
        #more advanced method for estimating availaibility based on the aggregator providing a fleet average IHL for the next timestep.
#            Mdot_fcst = np.multiply(self.Qheat, forecast_Mdot)
#            QIHL_mass_fcst = np.multiply(1-Sp1, forecast_IHL)
            
            Tair_Cf = Tair_ts
            Tfood_Cf = Tfood_ts
            
            
            # ts*60.0/
   
            dTairCf = 1.0/AC.C_Air*((forecast_Tind - Tair_Cf)/R_case + (Tfood_Cf-Tair_Cf)/R_food - self.C1 * Capacity(Tamb_ts) + 1 * self.Qheat + (forecast_Tind - Tair_Cf)*AC.m_dot_Cair * self.infil)   #*Mdot_ts  *Mdot_fcst
           
            dTfoodCf = 1.0/C_food * ((Tair_Cf - Tfood_Cf)/R_food)   #*(1-self.Sp3)
            
            
            Tair_Cff = Tair_Cf + dTairCf
            Tfood_Cff = Tfood_Cf + dTfoodCf
#            Twall_Cff = Twall_Cf + dTwallCf
#            Tattic_Cff = Tattic_Cf+dTatticCf
        
        Tair_forecast = Tair_Cff      


        if Tair_forecast >= (Tset - self.Tdeadband)-1 and Element_on_tsB == 0:  # and lockoffB >= 3*60.0
            isAvailable_add_ts = 1
        else:
            isAvailable_add_ts = 0

        if Tair_forecast <= (Tset + self.Tdeadband)+1 and Element_on_tsB > 0:
            isAvailable_shed_ts = 1
        else:
            isAvailable_shed_ts = 0

        # it isn't expected that the element would already be on due to the forecast temperature being below Tset- Tdeadband but are still expected to be below Tmax
        #  and Element_on_ts == 0
        # it is expected that the element would already be on due to the forecast temperature being below Tset + Tdeadband but are still expected to be above Tmin
        # and Element_on_ts > 0        
        
        Available_Capacity_Add = isAvailable_add_ts * E_cool
        Available_Capacity_Shed = isAvailable_shed_ts * E_cool
        

        response = RFResponse()
    
        # Report baseline response
        response.TairB = Tair_bas
        response.TfoodB = Tfood_bas
        response.TcaseB = Tcase_bas		

        response.ElementOnB = Element_on_bas		
        response.SOC_b = SOC_b		
        response.Pbase = Eused_baseline_ts			

        response.Tair = Tair_ts
        response.Tfood = Tfood_ts
        response.Tcase = Tcase_ts

        response.Tset = Tset_ts 
        response.Eused = Eused_ts

        response.lockoffB = lockoffB 
        response.lockonB = lockonB 
        response.lockoff = lockoff 
        response.lockon = lockon 
        response.sim_step = timestep

        response.cycle_off_grid = cycle_off_grid 
        response.cycle_on_grid = cycle_on_grid 




            Available_Capacity_Add = isAvailable_add_ts * E_cool
            Available_Capacity_Shed = isAvailable_shed_ts * E_cool
            
            PusedMin_ts = 0
            
            
            response = FRResponse()
        
            response.Tair = Tair_ts
            response.Tfood = Tfood_ts
#            response.Tset = Tset_ts 
            response.Eused = Eused_ts 
            response.PusedMax = PusedMax_ts
            response.PusedMin = PusedMin_ts
            response.ElementOn = Element_on_ts
            response.Eservice = float(Eservice_ts)
            # response.Estored = Estored
            response.SOC = SOC
            response.AvailableCapacityAdd = Available_Capacity_Add
            response.AvailableCapacityShed = Available_Capacity_Shed
            response.ServiceCallsAccepted = service_calls_accepted_ts
            response.IsAvailableAdd = isAvailable_add_ts
            response.IsAvailableShed = isAvailable_shed_ts
            
            return response    


            
#            return Tair_ts, Tfood_ts,  Eused_ts, PusedMax_ts, Element_on_ts, Eservice_ts, SOC, Available_Capacity_Add, Available_Capacity_Shed, service_calls_accepted_ts, isAvailable_add_ts, isAvailable_shed_ts
            # No direct calculation of Eloss_ts, 
            # , CountC, CountD, E_cool
#if __name__ == '__main__':
#    main()
        
  
#    
#    
#    

