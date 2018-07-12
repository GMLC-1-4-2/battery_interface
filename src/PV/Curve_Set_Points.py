# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 11:19:52 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def Curve_Set_Points():

    import PV_Inverter_Data
    import numpy as np

    [Efficiency,Vdc,DC_Power,Rating,F_P,F_Q,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
    [P_rated,P_min,S_max,Qmax_Plus,Qmax_Minus]=Rating

    #%% volt-var settings
    Volt_Var_V=[0, 0.9, .98, 1.02, 1.1, 2]
    Volt_Var_Var=[Qmax_Plus, Qmax_Plus, 0, 0, Qmax_Minus, Qmax_Minus]
    Volt_Var=[Volt_Var_V,Volt_Var_Var]
    
    #%% Volt-watt settings
    Volt_Watt_Volt=[0, 1.05, 1.1, 2]
    Volt_Watt_Watt=[P_rated, P_rated, np.maximum(0.2*P_rated,P_min), np.maximum(0.2*P_rated,P_min)]
    Volt_Watt=[Volt_Watt_Volt,Volt_Watt_Watt]
    
    #%% frequency-watt settings
    dbUF=0.036
    dbOF=0.036
    kUF=0.05
    kOF=0.05
    Freq_Watt=[dbUF,dbOF,kUF,kOF]    
     
    return Volt_Var,Volt_Watt,Freq_Watt
    
        
