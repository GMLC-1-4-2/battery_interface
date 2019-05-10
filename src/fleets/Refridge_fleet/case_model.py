# -*- coding: utf-8 -*-
"""
Created on June 2018
For GMLC 1.4.2, generate the desired case thermal model 
A simplified grey-box refrigerator (case) thermal model was developed, and parameters were trained based on measured data from the medium temperature supermarket CO2 refrigeration system

Last update: 05/07/2019
Version: 1.0

States 
X = [Tair Tfood Tcase]'

Control 
u = [Qac_i]

@author: Jin Dong, Borui Cui, Jian Sun, Jeffrey Munk, Teja Kuruganti
ORNL
""

"""

# depending on the IDE used these libraries might need to be imported manually

from fleets.Refridge_fleet.fridge_Response import RFResponse

import numpy as np
import control
import pandas as pd

#########################################################################
# define system model

shortcycle = 2*60.0 # seconds minimum time that unit has to stay off before turning back on
minrun = 1*60.0 # seconds minimum runtime for unit

class AC_RF: # compressor model for MT CO2 refrigerator!
    b0=3677.089459   
    b1=-115.2126198
    b2=-0.909689722
    b3=5.977244154
    b4=0.478541268
    b5=1.707071315
    b6=38545.43758
    b7=895.2242371
    b8=3.439209561
    b9=-427.6732271
    b10=1.427300647
    b11=-7.221110318
    k0=0.861088
    k1=-0.00307
    k2=-0.000042
    k3=0.0000039

def WMT(self, Tambient, SMT=13.36):

    TambientF = Tambient *9.0/5.0 + 32
    if TambientF<41:
        self.SDT=46.791-0.0214*TambientF
    elif TambientF>=72:
        self.SDT=77
    else:
        self.SDT=TambientF+5
    self.CFMT=AC_RF.k0+AC_RF.k1*SMT+AC_RF.k2*self.SDT+AC_RF.k3*SMT*self.SDT
    return(self.CFMT*(AC_RF.b0+AC_RF.b1*SMT+AC_RF.b2*SMT*SMT+AC_RF.b3*self.SDT+AC_RF.b4*self.SDT*self.SDT+AC_RF.b5*SMT*self.SDT))

def QMT(self, Tambient, SMT=13.36):

    TambientF = Tambient *9.0/5.0 + 32
    if TambientF<41:
        self.SDT=46.791-0.0214*TambientF
    elif TambientF>=72:
        self.SDT=77
    else:
        self.SDT=TambientF+5
    self.CFMT=AC_RF.k0+AC_RF.k1*SMT+AC_RF.k2*self.SDT+AC_RF.k3*SMT*self.SDT
    return(self.CFMT*(AC_RF.b6+AC_RF.b7*SMT+AC_RF.b8*SMT*SMT+AC_RF.b9*self.SDT+AC_RF.b10*self.SDT*self.SDT+AC_RF.b11*SMT*self.SDT))



#################################################################


#Case characteristics    

class CaseModel():
    def __init__(self, Tamb = 25.0, Tset = 6, R_case=0.044077, R_food=0.004614, R_infil=0.008341, C_case=10200510, C_food=2844769, 
                    C_air=111053.5, time_step = 10, 
                    Element_onB = 0, Element_on = 0, lockonB = 0, lockoffB = 0,  lockon = 0, lockoff = 0, cycle_off_base = 0, 
                    cycle_on_base = 0, cycle_off_grid = 0, cycle_on_grid = 0):
        # RF Characteristic Information           
        
        
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
        
        self.Tambient = [20.0]
        
        
        self.Tdeadband = 2
        self.Tmin = 4 # deg C
        self.Tmax = 8 # deg C            
    
    # def execute(self, Tair, Tfood, Tcase, Tset, Tamb, R_case, R_food, R_infil, C_case, C_food, C_air, control_signal, timestep, Element_on, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid):
        # # (Tin, Twall, Tmass, Tattic, Tset, Eused, PusedMax, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available_add, is_available_shed) = self.HVAC(Tin, Twall, Tmass,  Tattic, Tset, Tamb, Tsol_w, QIHL_i, Qsolar_i, Tsol_r, QIHL_mass, Qsolar_mass, Rwall, Rattic, Cmass, control_signal, 
        # #      service_calls_accepted, Element_on, self.max_service_calls, timestep, forecast_IHL, IsForecast)
        # (response) = self.FRIDGE(Tair, Tfood, Tcase, Tset, Tamb, R_case, R_food, R_infil, C_case, C_food, C_air, control_signal, 
                # timestep, Element_on, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid)
        
        # return response

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
        # PusedMax_ts = 1e-3*Capacity(AC,Tamb_ts)*EIR(AC,Tamb_ts)   # max instant power (EIR or COP is changing)         
        # Element_on_ts = 0        

        # Record control states          
        # switch on
        if Tair_lastB > Tset + self.Tdeadband and lockoffB >= 3*60.0:  # and Element_on_tsB == 0 
            Element_on_tsB = 1
            Eused_baseline_ts = E_cool*1.000 # kW used
            cycle_on_base += 1 #count cycles turning from off to on
            # lockonB = 1*ts # start recording on period
            lockoffB += 1*ts

        # switch off
        elif Tair_lastB <= (Tset - self.Tdeadband):
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

#        Calculate more parameters to be passed up
#       update SoC
        SOC_b = (Tset + self.Tdeadband - Tair_bas)/(Tset + self.Tdeadband - (Tset - self.Tdeadband))         
        if SOC_b >= 1:
            SOC_b = 1 
        elif SOC_b <= 0:
            SOC_b = 0
        

        ###########################################################################          
                # Modify operation based on control signal #
                # Reduce loads

        ###########################################################################          
            #modify operation based on control signal 
            # Assumed to work in Summer Cooling Only!
        #TODO: temporary code for integration testing while I figure out where to track max service calls
        service_calls_accepted_ts = 0
        
        # Reduce loads 
        if control_signal_ts  > 0 and Element_on_tsB == 1 and Tair_last < (Tset + self.Tdeadband): #Element_on_ts = 1 requirement eliminates free rider situation  
            Eused_ts = 0 #make sure it stays off
            Element_on_ts = 0
            service_calls_accepted_ts += 1
            cycle_off_grid += 1
            lockoff = 1*ts # start recording on period

        # elif control_signal_ts  > 0 and Tair_last >= Tset + self.Tdeadband:
            # # don't change anything
            # Eused_ts = Eused_baseline_ts
            
        # # Increase loads    
        # elif control_signal_ts  < 0 and Tair_last <= Tset - self.Tdeadband:
            # Eused_ts = 0 #make sure it stays off
            # Element_on_ts = 0
    
        elif control_signal_ts  < 0 and Tair_last >= (Tset - self.Tdeadband) and Element_on_tsB == 0 and lockoff >= 3*60.0: #Element_on_ts = 0 requirement eliminates free rider situation  
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

        Eservice_ts = Eused_baseline_ts - Eused_ts
   
        #could change this at some point based on signals
        Tset_ts = Tset    
        
        # Evolution of 3 states

        dTair=((Tamb_ts-Tair_last)/R_infil + (Tfood_last-Tair_last)/R_food + (Tcase_last-Tair_last)/R_case - Element_on_ts*self.C1*QMT(AC_RF, Tamb_ts)*self.Sp1)/C_air/ts #x1 is Tair
        dTfood=((Tair_last-Tfood_last)/R_food)/C_food/ts #x2 is Tfood
        dTcase=((Tair_last-Tcase_last)/R_case - Element_on_ts*self.C1*QMT(AC_RF, Tamb_ts)*(1-self.Sp1))/C_case/ts #x3 is Tcase   
                        
        Tair_ts = Tair_last + dTair 
        Tfood_ts = Tfood_last + dTfood
        Tcase_ts = Tcase_last + dTcase            
        
#            dT_power_input = Eused_ts*timestep*60/(3.79*self.Capacity*4810) #timestep is in minutes so mult by 60 to get seconds

#        Calculate more parameters to be passed up
#       update SoC
        SOC = (Tset + self.Tdeadband - Tair_ts)/(Tset + self.Tdeadband - (Tset - self.Tdeadband))
        if SOC >= 1:
            SOC = 1 
        elif SOC <= 0:
            SOC = 0
    
#   isAvailable_add_ts = 1 if max_service_calls > service_calls_accepted_ts  else 0
######################################################################################        
#simple method to forecast availability for providing a service during next timestep
        
        Tair_Cf = Tair_ts
        Tfood_Cf = Tfood_ts
        Tcase_Cf = Tcase_ts                      

        dTairCf=((Tamb_ts-Tair_Cf)/R_infil + (Tfood_Cf-Tair_Cf)/R_food + (Tcase_Cf-Tair_Cf)/R_case - Element_on_ts*self.C1*QMT(AC_RF, Tamb_ts)*self.Sp1)/C_air/ts #x1 is Tair
        dTfoodCf=((Tair_Cf-Tfood_Cf)/R_food)/C_food/ts #x2 is Tfood
        dTcaseCf=((Tair_Cf-Tcase_Cf)/R_case - Element_on_ts*self.C1*QMT(AC_RF, Tamb_ts)*(1-self.Sp1))/C_case/ts #x3 is Tcase        
        
        Tair_Cff = Tair_Cf + dTairCf
#            Tmass_Cff = Tmass_Cf+dTmassCf
#            Twall_Cff = Twall_Cf + dTwallCf
#            Tattic_Cff = Tattic_Cf+dTatticCf
        
        Tair_forecast = Tair_Cff      

        isAvailable_add_ts = 1 if Tair_forecast > (Tset - self.Tdeadband)-2 > 0 else 0 # it isn't expected that the element would already be on due to the forecast temperature being below Tset- Tdeadband but are still expected to be below Tmax
        #  and Element_on_ts == 0
        isAvailable_shed_ts = 1 if Tair_forecast < (Tset + self.Tdeadband)+2 > 0 else 0 # it is expected that the element would already be on due to the forecast temperature being below Tset + Tdeadband but are still expected to be above Tmin
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

        response.cycle_off_base = cycle_off_base 
        response.cycle_on_base = cycle_on_base

        response.ElementOn = Element_on_ts
        response.Eservice = Eservice_ts
        # response.Estored = Estored
        response.SOC = SOC

        response.AvailableCapacityAdd = Available_Capacity_Add
        response.AvailableCapacityShed = Available_Capacity_Shed
        response.ServiceCallsAccepted = service_calls_accepted_ts
        response.IsAvailableAdd = isAvailable_add_ts      
        response.IsAvailableShed = isAvailable_shed_ts              

        # Report grid services response
        return response    

if __name__ == '__main__':
   main()
        
  
#    
#    
#    

