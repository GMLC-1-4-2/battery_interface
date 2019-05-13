# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 15:07:49 2018
For GMLC 1.4.2, generate the desired building thermal model and HVAC model
High level 4R4C model

Last update: 05/09/2019
Version: 1.0

States 
X = [Tin  Twall  Tmass Tattic]'

Control 
u = [Qac_i,  Qac_mass]

Outdoor Disturbance 
V = [ Tsol_w,   QIHL_i,   Qsolar_i;   Tsol_r,   QIHL_mass,   Qsolar_mass]

Function Inputs
    Parametrs: Sp1, Sp2, Sp3, Rext, Rattic, Cmass,
    DIscretization Interval: Interval

HVAC model is a polynomial fit of Tout and Tin
From manufacture name plate performance curve

@author: Jin Dong, Jeffrey Munk, Borui Cui, Teja Kuruganti
ORNL
"""

# depending on the IDE used these libraries might need to be imported manually

from fleets.HVAC_fleet.AC_Response import ACResponse

import numpy as np
import control
import pandas as pd

#########################################################################
# define HVAC COP related with Tout Tin

Tin_assumed=17.2222222

shortcycle = 5*60.0 # seconds minimum time that AC unit has to stay off before turning back on
minrun = 1*60.0 # seconds minimum runtime for unit

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

AC=AC(13800*1.15,0.30839)  # rated 4900 W

#Column names for weather input data
class c():
    COL_TOUT='Dry-bulb (C)'
    COL_H='Hconvection'
    COL_QIHL='QIHL (W)'
    COL_RADW='Radwall (W/m^2)'
    COL_RADR='Radroof (W/m^2)'
    COL_RADWIN='Radwindow (W/m^2)'
    COL_DATETIME='Date/Time'

def Capacity(AC,Tout,Tin=Tin_assumed):
    return((AC.C1+AC.C2*Tin+AC.C3*Tin*Tin+AC.C4*Tout+AC.C5*Tout*Tout+AC.C6*Tout*Tin)*AC.Qrated)
    
def EIR(AC,Tout,Tin=Tin_assumed):
    return((AC.C7+AC.C8*Tin+AC.C9*Tin*Tin+AC.C10*Tout+AC.C11*Tout*Tout+AC.C12*Tout*Tin)*AC.EIRrated)        

# Elec power consump will be Capacity * EIR (kW)
#################################################################

#SHR equation derived from apparatus dew point (ADP) method used by EnergyPlus for BEopt 2.7 AC    
def SHR(Tout,Tdb,Twb):
    return(0.64613+0.003183*Tdb-.08153*Twb+.059996*Tdb)

#Building characteristics    
# class building:
#     def __init__(self,T_in,T_mass,T_wall,T_attic,Rwall=0.00852, Rattic=0.03441,Rwin=0.00702,SHGC=0.4,Cwall=6719515.27,Cin=8666569.0,C1=0.73244,C2=0.49534,C3=0.05,Cattic=501508.7,Rroof=0.002,Cmass=29999128.0,Rmass=.00661,Sp1=0.93,Sp2=0.10006,Sp3=0.92997, Qrated=14600, EIRrated=0.31019, TinWB=16.666667,Initial_On=0):
#         self.T_in=T_in
#         self.T_mass=T_mass
#         self.T_wall=T_wall
#         self.T_attic=T_attic
#         self.Rwall=Rwall
#         self.Rattic=Rattic
#         self.Cwall=Cwall
#         self.Cin=Cin
#         self.C1=C1
#         self.C2=C2
#         self.C3=C3
#         self.Cattic=Cattic
#         self.Rroof=Rroof
#         self.Cmass=Cmass
#         self.Rmass=Rmass
#         self.Sp1=Sp1
#         self.Sp2=Sp2
#         self.Sp3=Sp3
#         self.Qrated=Qrated
#         self.EIRrated=EIRrated
#         self.TinWB=TinWB
#         self.Rwin=Rwin
#         self.SHGC=SHGC
#         self.Initial_On=Initial_On

class BuildingModel():
    def __init__(self, Tamb = 25.0, Tsol_w = [25.0],QIHL_i = [0], Qsolar_i = [0], 
                    Tsol_r = [25.0], QIHL_mass = [0], Qsolar_mass = 0,  
                    Rwall = 0.00852, Rattic = 0.034141, 
                    Cmass = 29999128.0, time_step = 10, 
                    forecast_IHL = 0, Element_onB = 0, Element_on = 0, lockonB = 0, lockoffB = 0, lockon = 0, lockoff = 0, cycle_off_base = 0, 
                    cycle_on_base = 0, cycle_off_grid = 0, cycle_on_grid = 0):
        # Building Thermal Characteristic Information
    
        # These three as input variables dependant on Envelope types
#            self.Rwall=.00852  # without multiplier is CC1
#            self.Rattic=.03441 # without multiplier is CC1
#            self.Cmass=29999128.0
        
        self.Cwall=6719515.27
        self.Cin=8666569.0
        self.C1=0.73244
        self.C2=0.49534
        self.C3=0.05
        self.Cattic=501508.7
        self.Rroof=0.002        
        self.Rmass=.00661
        # Splitting coefficients for HVAC cooling
        self.Sp1=0.93
        self.Sp2=0.10006
        self.Sp3=0.92997
        
        self.QIHL = [0]
        self.QHVAC = [0]
        self.Qsolar = [0]
        self.solar_irradiance = [0]
        self.H_convection_roof = [11.0]
        self.alpha_absorption_roof = [.54] #[0.9]
        self.H_convection_wall = [11.0]
        self.alpha_absorption_wall = [0.2] #[0.3]
        self.dt = [time_step*60.0]   # in seconds discretization

        self.Twall = [23.33]
        self.Tin = [23.0]
        self.Tattic = [23.8]
        self.Tim = [23.5]
        
        self.Tambient = [25.0]
        self.Tsol_roof = [25.0]
        self.Tsol_wall = [25.0] 
        # self.max_service_calls = int(max_service_calls)
        
        self.Tdeadband = 1
        self.Tmin = 22 # deg C
        self.Tmax = 24 # deg C            
        
        #############################################################################
        # Validated 2-story single family house model CC1
        # state-space model to check the controllability and simplify the design of MPC (in the future)           
                    
#############################################################################
    # def Capacity(AC,Tout,Tin=Tin_assumed):
    #     return((AC.C1+AC.C2*Tin+AC.C3*Tin*Tin+AC.C4*Tout+AC.C5*Tout*Tout+AC.C6*Tout*Tin)*AC.Qrated)
        
    # def EIR(AC,Tout,Tin=Tin_assumed):
    #     return((AC.C7+AC.C8*Tin+AC.C9*Tin*Tin+AC.C10*Tout+AC.C11*Tout*Tout+AC.C12*Tout*Tin)*AC.EIRrated)
        
        
    # def execute(self, Tin, Twall, Tmass,  Tattic, Tset, Tamb, Tsol_w, QIHL_i, Qsolar_i, Tsol_r, QIHL_mass, Qsolar_mass, Rwall, Rattic, Cmass, control_signal, timestep, forecast_IHL, Element_on, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid):
    #     # (Tin, Twall, Tmass, Tattic, Tset, Eused, PusedMax, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available_add, is_available_shed) = self.HVAC(Tin, Twall, Tmass,  Tattic, Tset, Tamb, Tsol_w, QIHL_i, Qsolar_i, Tsol_r, QIHL_mass, Qsolar_mass, Rwall, Rattic, Cmass, control_signal, 
    #     #      service_calls_accepted, Element_on, self.max_service_calls, timestep, forecast_IHL, IsForecast)
    #     (response) = self.HVAC(Tin, Twall, Tmass,  Tattic, Tset, Tamb, Tsol_w, QIHL_i, Qsolar_i, Tsol_r, QIHL_mass, Qsolar_mass, Rwall, Rattic, Cmass, control_signal, 
    #             timestep, forecast_IHL, Element_on, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid)
        
    #     return response

    def HVAC(self, TlastB, Twall_lastB, Tmass_lastB, Tattic_lastB, Tlast, Twall_last, Tmass_last, Tattic_last, Tset, Tamb_ts, Tsol_w_ts, 
                QIHL_i_ts, Qsolar_i_ts, Tsol_r_ts, QIHL_mass_ts, Qsolar_mass_ts, Rwall, Rattic, Cmass, control_signal_ts, 
                timestep, forecast_IHL, Element_on_tsB, Element_on_ts, lockonB, lockoffB, lockon, lockoff, cycle_off_base, cycle_on_base, cycle_off_grid, cycle_on_grid):


        #############################################################################
                #        Baseline operation - Base Loads
        #############################################################################
        BM = BuildingModel
        ts = timestep
        # ts = 10

        shortcycle_ts = int(round(shortcycle/ts,0))  #number of time steps during short cycle timer
        minrun_ts = int(round(minrun/ts,0))
            
        # estimate on what the maximum power usage could be
        E_cool= 1e-3*Capacity(AC,Tamb_ts)*EIR(AC,Tamb_ts)     # power consumpstion in kW
        # Eused_baseline_ts = 0
        # PusedMax_ts = 1e-3*Capacity(AC,Tamb_ts)*EIR(AC,Tamb_ts)   # max instant power (EIR or COP is changing)         
        # Element_on_ts = 0        

        # Record control states          
        # switch on
        if TlastB > (Tset + self.Tdeadband) and Element_on_tsB == 0 and lockoffB >= 2*60.0:   # and Element_on_tsB == 0 
            Element_on_tsB = 1
            Eused_baseline_ts = E_cool*1.000 # kW used
            cycle_on_base += 1 #count cycles turning from off to on
            # lockonB = 1*ts # start recording on period
            lockoffB += 1*ts

        # switch off
        elif TlastB <= (Tset - self.Tdeadband) and Element_on_tsB == 1:  #and lockonB >= 1*60.0
            Eused_baseline_ts = 0 # kW used
            Element_on_tsB = 0
            cycle_off_base += 1  # count cycles  turning from ON to OFF
            lockoffB = 1*ts # start recording off period
            # lockonB = 0

        # no change
        else:
            Eused_baseline_ts = Element_on_tsB * E_cool

            # lockonB += 1*ts
            lockoffB += 1*ts # cumulating recording off period      
            # if Element_on_tsB:
            #     lockonB += 1*ts
            # else:
            #     lockoffB += 1*ts # cumulating recording off period   

        # Record baseline states
        # Evolution of 4 states, ts in seconds                
                    
        dTin_baseline = ts/self.Cin*((Twall_lastB-TlastB)*2.0/Rwall+(Tattic_lastB-TlastB)/Rattic+
                 (Tmass_lastB-TlastB)/self.Rmass + QIHL_i_ts * self.C1 + Qsolar_i_ts*self.C3 -
                 Element_on_tsB*Capacity(AC,Tamb_ts)*self.C2)   #*self.Sp3
        
        dTmass_baseline = ts/Cmass*((TlastB-Tmass_lastB)/self.Rmass + QIHL_mass_ts*self.C1+
                   Qsolar_mass_ts*self.C3 - Element_on_tsB*Capacity(AC,Tamb_ts)*self.C2)   #*(1-self.Sp3)
        
        dTwall_baseline = ts/self.Cwall*((Tsol_w_ts - Twall_lastB)*2.0/Rwall+(TlastB -Twall_lastB)*2.0/Rwall)

        dTattic_baseline = ts/self.Cattic*((Tsol_r_ts-Tattic_lastB)/self.Rroof + (TlastB - Tattic_lastB)/Rattic)
            
        # Store for output metric data
        Tin__bas = TlastB + dTin_baseline   # Store the baseline indoor temperature    
        Twall_bas = Twall_lastB + dTwall_baseline
        Tmass_bas = Tmass_lastB + dTmass_baseline
        Tattic_bas = Tattic_lastB + dTattic_baseline

        Element_on_bas = Element_on_tsB      

        # update baseline SoC
        SOC_b = (Tset + self.Tdeadband - Tin__bas)/(Tset + self.Tdeadband - (Tset - self.Tdeadband))  

        if SOC_b >= 1:
            SOC_b = 1 
        elif SOC_b <= 0:
            SOC_b = 0      

        ###########################################################################          
        # Modify operation based on control signal #
        # Reduce loads
 
        ###########################################################################          
        # modify operation based on control signal 
        # Assumed to work in Summer Cooling Only! 
        # need adjust temperature signs for heating case    
           
        service_calls_accepted_ts = 0
        
        # Reduce loads 
        if control_signal_ts  > 0 and Tlast < (Tset + self.Tdeadband) and Element_on_tsB == 1: #Element_on_ts = 1 requirement eliminates free rider situation  and lockoff >= 3*60.0
            Eused_ts = 0 #make sure it stays off
            Element_on_ts = 0
            service_calls_accepted_ts += 1
            cycle_off_grid += 1
            # lockon = 1*ts
            lockoff = 1*ts # start recording on period

        # elif control_signal_ts  > 0 and Tlast >= Tset + self.Tdeadband:
        #     # don't change anything
        #     Eused_ts = Eused_baseline_ts
            
        # Increase loads    
        # elif control_signal_ts  < 0 and Tlast <= Tset - self.Tdeadband:
        #     Eused_ts = 0 #make sure it stays off
        #     Element_on_ts = 0
    

        elif control_signal_ts  < 0 and Tlast >= (Tset - self.Tdeadband) and Element_on_tsB == 0 and lockoff >= 2*60.0: #Element_on_ts = 0 requirement eliminates free rider situation   

            #make sure it stays on
            Eused_ts = E_cool*1.000 #W used
            Element_on_ts = 1
            service_calls_accepted_ts += 1
            cycle_on_grid += 1
            lockoff += 1*ts # start recording on period

        else:#no changes
            Eused_ts = Eused_baseline_ts
            # lockon += 1*ts
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

        Eservice_ts = Eused_baseline_ts - Eused_ts # positive means reducing power consumption         
        
        #could change this at some point based on signals
        Tset_ts = Tset    
        
        # Evolution of 4 states under grid services          
        dTin = ts/self.Cin*((Twall_last-Tlast)*2.0/Rwall+(Tattic_last-Tlast)/Rattic+
                    (Tmass_last-Tlast)/self.Rmass + QIHL_i_ts * self.C1 + Qsolar_i_ts*self.C3 -
                    Element_on_ts*Capacity(AC,Tamb_ts)*self.C2)   #*self.Sp3
        
        dTmass = ts/Cmass*((Tlast-Tmass_last)/self.Rmass + QIHL_mass_ts*self.C1+
                    Qsolar_mass_ts*self.C3 - Element_on_ts*Capacity(AC,Tamb_ts)*self.C2)   #*(1-self.Sp3)
        
        dTwall = ts/self.Cwall*((Tsol_w_ts - Twall_last)*2.0/Rwall+(Tlast -Twall_last)*2.0/Rwall)
        
        dTattic = ts/self.Cattic*((Tsol_r_ts-Tattic_last)/self.Rroof + (Tlast - Tattic_last)/Rattic)
            
        Tin_ts = Tlast + dTin 
        Twall_ts = Twall_last + dTwall
        Tmass_ts = Tmass_last + dTmass
        Tattic_ts = Tattic_last + dTattic      

#        Calculate more parameters to be passed up
#       update SoC
        SOC = (Tset + self.Tdeadband - Tin_ts)/(Tset + self.Tdeadband - (Tset - self.Tdeadband))
        if SOC >= 1:
            SOC = 1 
        elif SOC <= 0:
            SOC = 0
    
#            isAvailable_add_ts = 1 if max_service_calls > service_calls_accepted_ts  else 0
######################################################################################        
    #simple method to forecast availability for providing a service during next timestep
#        isAvailable_ts = 1 if max_service_calls > service_calls_accepted_ts  else 0
    #more advanced method for estimating availaibility based on the aggregator providing a fleet average IHL for the next timestep.
        QIHL_i_fcst = np.multiply(self.Sp1, forecast_IHL)
#            QIHL_mass_fcst = np.multiply(1-Sp1, forecast_IHL)
       
        Tin_Cf = Tin_ts
        Twall_Cf = Twall_ts
        Tmass_Cf = Tmass_ts
        Tattic_Cf = Tattic_ts            
        
        dTinCf=ts/self.Cin*((Twall_Cf-Tin_Cf)*2.0/Rwall+(Tattic_Cf-Tin_Cf)/Rattic+
                        (Tmass_Cf-Tin_Cf)/self.Rmass + QIHL_i_fcst * self.C1*self.Sp1 + Qsolar_i_ts*0.56*25.76*self.C3*self.Sp2-
                        Capacity(AC,Tamb_ts)*self.C2*self.Sp3)
            
        dTmassCf=ts/Cmass*((Tin_Cf-Tmass_Cf)/self.Rmass + QIHL_i_fcst*self.C1*(1-self.Sp1)+
                    Qsolar_mass_ts*0.56*25.76*self.C3*(1-self.Sp2)-Capacity(AC,Tamb_ts)*self.C2*(1-self.Sp3))
        
        dTwallCf=ts/self.Cwall*((Tsol_w_ts - Twall_Cf)*2.0/Rwall+(Tin_Cf -Twall_Cf)*2.0/Rwall)
        
        dTatticCf=ts/self.Cattic*((Tsol_r_ts-Tattic_Cf)/self.Rroof + (Tin_Cf - Tattic_Cf)/Rattic)
        
        Tin_Cff = Tin_Cf + dTinCf
#            Tmass_Cff = Tmass_Cf+dTmassCf
#            Twall_Cff = Twall_Cf + dTwallCf
#            Tattic_Cff = Tattic_Cf+dTatticCf
        

        Tin_forecast = Tin_Cff     

        if Tin_forecast >= (Tset - self.Tdeadband)-1 and Element_on_tsB == 0:  # and lockoffB >= 3*60.0
            isAvailable_add_ts = 1
        else:
            isAvailable_add_ts = 0

        if Tin_forecast <= (Tset + self.Tdeadband)+1 and Element_on_tsB > 0:
            isAvailable_shed_ts = 1
        else:
            isAvailable_shed_ts = 0

        # isAvailable_add_ts = 1 if Tin_forecast > (Tset - self.Tdeadband)-1  > 0 else 0 #It isn't expected that the element would already be on due to the forecast temperature being below Tset- Tdeadband but are still expected to be below Tmax
        # # and Element_on_ts == 0  and Element_on_tsB == 0
        # isAvailable_shed_ts = 1 if Tin_forecast < (Tset + self.Tdeadband)+1  > 0 else 0  #It is expected that the element would already be on due to the forecast temperature being below Tset + Tdeadband but are still expected to be above Tmin
        # # and Element_on_ts > 0 and Element_on_tsB > 0


        Available_Capacity_Add = isAvailable_add_ts * E_cool
        Available_Capacity_Shed = isAvailable_shed_ts * E_cool
       
        response = ACResponse()
    
        # Report baseline response
        response.TinB = Tin__bas
        response.TwallB = Twall_bas
        response.TmassB = Tmass_bas
        response.TatticB = Tattic_bas
        
        response.ElementOnB = Element_on_bas
        response.SOC_b = SOC_b
        response.Pbase = Eused_baseline_ts

        # Report grid service response
        response.Tin = Tin_ts
        response.Twall = Twall_ts
        response.Tmass = Tmass_ts
        response.Tattic = Tattic_ts
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
        response.Eservice = Eservice_ts  #float()
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

