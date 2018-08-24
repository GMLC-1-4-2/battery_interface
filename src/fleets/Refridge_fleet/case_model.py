# -*- coding: utf-8 -*-
"""
Created on June 2018
For GMLC 1.4.2, generate the desired case thermal model 
High level 2R2C model

Last update: 08/06/2018
Version: 1.0

States 
X = [Tcase  Tfood]'

Control 
u = [Qac_i]

----------
Parameters:

Case Volume	131.13	ft^3
Product Volume fraction	0.6	
Air Volume	52.452	ft^3
Air Mass	3.9339	lb
Air C	0.944136	Btu/R
Air C	1793.03106	J/K
Product Volume	78.678	ft^3
Product fraction water	0.5	
Product Air Mass	2.950425	lb
Product Water Mass	2439.018	lb
Product Air C	0.708102	Btu/R
Product Water C	2439.018	Btu/R
Product C	2439.726102	Btu/R
Product C	4633341.678	J/K
Discharge Air Velocity	200	fpm
Discharge grille length	12	ft
Discharge grille width	0.333333333	ft
Discharge Volume flow	800	cfm
Max Infil Coeff	864	Btu/h-F
Max Infil Coeff	455.7896896	W/K
Case length	12	ft
Case Height	6.833333333	ft
Case Depth	3	ft
Case Surface	195	ft^2
R-Value	10	h-ft^2-F/Btu
Rcase	0.051282051	h-F/Btu
Rcase	0.097210826	K/W
Product Surface Area	460	ft^2
h	3.5	Btu/h-ft^2-R
Rfood	0.000621118	h-F/Btu
Rfood	0.001177398	K/W

@author: dongj@ornl.gov
ORNL
"""

# depending on the IDE used these libraries might need to be imported manually

import numpy as np
#import control
import pandas as pd

#########################################################################


class c():
    COL_TAMB="T_ia (F)"
    COL_TSUP="T_a5_up (F)"
    COL_TRET="T_a5_low (F)"
    COL_TEVAP="Tevap"
    COL_PEVAP="P_a5_suc (psig)"
    COL_TTXV="T_a5_eev_l (F)"
    COL_PLIQ="P_a5_liq (psig)"
    COL_MDOT="M_a5 (lb/min)"  # = 0.00755985 kg/s
    COL_TAIR="T_a5_avg"
    COL_TFOOD="MTCase-TC Ave (F)"
    COL_QSENS="Qsens"

class AC:
        C_Air = 1793.031*6   # of the case air J/K
        m_dot_Cair = 455.7897
#        infil = 455.7896896  # W/K
        
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
    
def COP(Tout):
    return(-0.04418*Tout + 3.5892)   #Tout in C      1.8 ~ 2.9   

# Elec power consump will be Capacity * EIR (kW)
#################################################################

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
            
            
        def execute(self, Tair, Tfood, Tamb, Tind, R_case, R_food, C_food, control_signal, service_calls_accepted, Element_on, timestep, forecast_Tind, IsForecast):
            (Tair, Tfood, Eused, PusedMax, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available_add, is_available_shed) = self.FRIDGE(Tair, Tfood, Tamb, Tind, R_case, R_food, C_food, control_signal, 
                 Element_on, service_calls_accepted, self.max_service_calls, timestep, forecast_Tind, IsForecast)
            
            return Tair, Tfood, Eused, PusedMax, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available_add, is_available_shed, 
    
        def FRIDGE(self, Tair_last, Tfood_last, Tamb_ts, Tind_ts, R_case, R_food, C_food, control_signal_ts, 
                 Element_on_ts, service_calls_accepted_ts, max_service_calls, timestep, forecast_Tind, is_forecast):
        
        
#############################################################################
        #        Baseline operation - Base Loads
#############################################################################
#            BM = BuildingModel
            ts = timestep
                
          #estimate on what the maximum power usage could be
            E_cool= 1.000*Capacity(Tamb_ts)/COP(Tamb_ts)     # power consumpstion in W
            Eused_baseline_ts = 0
            PusedMax_ts = Capacity(Tamb_ts)/COP(Tamb_ts)   # max instant power (EIR or COP is changing)
 
            # Record control states          
            if Tfood_last > self.T_food_set + self.Tdeadband or Tair_last > self.T_air_set + self.Tdeadband:
                Eused_baseline_ts = E_cool*1.000 #W used
                Element_on_ts = 1
            elif Element_on_ts == 1 and Tfood_last > self.T_food_set - self.Tdeadband and Tair_last > self.T_air_set - self.Tdeadband:
                Eused_baseline_ts = E_cool*1.000 #W used
                Element_on_ts = 1
            else:
                Eused_baseline_ts = 0
                Element_on_ts = 0


#            print(Element_on_ts)                
###########################################################################          
            # Modify operation based on control signal #
            # Reduce loads
            if control_signal_ts  < 0 and Tfood_last < self.T_food_max and Tair_last < self.T_air_max and Element_on_ts == 1: #Element_on_ts = 1 requirement eliminates free rider situation
                Eused_ts = 0 #make sure it stays off
                Element_on_ts = 0
                service_calls_accepted_ts += 1
      
            elif control_signal_ts  < 0 and Tfood_last >= self.T_food_max or Tair_last >= self.T_air_max:
                # don't change anything
                Eused_ts = Eused_baseline_ts
                
            # Increase loads    
            elif control_signal_ts  > 0 and Tfood_last <= self.T_food_min or Tair_last <= self.T_air_min:
                Eused_ts = 0 #make sure it stays off
                Element_on_ts = 0
             
            elif control_signal_ts  > 0 and Tfood_last >= self.T_food_min  and Element_on_ts == 0: #and Tair_last >= self.T_air_min Element_on_ts = 0 requirement eliminates free rider situation
                #make sure it stays on
                Eused_ts = E_cool*1.000 #W used
                Element_on_ts = 1
                service_calls_accepted_ts += 1
           
            else:#no changes
                Eused_ts = Eused_baseline_ts
            
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
            Tfood_forecast = Tfood_Cff 
            
            # and Tair_forecast >= self.T_air_min  
            isAvailable_add_ts = 1 if Tfood_forecast >= self.T_food_min and Element_on_ts == 0 > 0 else 0 #haven't exceeded max number of calls, plus it isn't expected that the element would already be on due to the forecast temperature being below Tset- Tdeadband but are still expected to be below Tmax
            # and Tair_forecast <= self.T_air_max 
            isAvailable_shed_ts = 1 if Tfood_forecast <= self.T_food_max and Element_on_ts > 0 > 0 else 0  #haven't exceeded max number of calls, plus it is expected that the element would already be on due to the forecast temperature being below Tset + Tdeadband but are still expected to be above Tmin



            Available_Capacity_Add = isAvailable_add_ts * E_cool
            Available_Capacity_Shed = isAvailable_shed_ts * E_cool


            
            return Tair_ts, Tfood_ts,  Eused_ts, PusedMax_ts, Element_on_ts, Eservice_ts, SOC, Available_Capacity_Add, Available_Capacity_Shed, service_calls_accepted_ts, isAvailable_add_ts, isAvailable_shed_ts
            # No direct calculation of Eloss_ts, 
            # , CountC, CountD, E_cool
#if __name__ == '__main__':
#    main()
        
  
#    
#    
#    

