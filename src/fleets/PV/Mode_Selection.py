# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 11:17:54 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""

#%% Mode selection

def Mode_Selection(Auto_Direct_Mode,Auto_Modes,Pmpp_AC,P_Pre,P_Direct,Q_Direct,PF,V,f,f_nom):
    
    #%Auto_Direct_Mode=1; % select 1 for autonomous and 2 for direct command
    
    #% Auto_Modes=1: frequency-watt
   # % Auto_Modes=2:  Volt-watt
    #% Auto_Modes=3: power factor
   # % Auto_Modes=4: volt-var 
    
   # %% Autonomous mode
    from scipy.interpolate import interp1d
    import numpy as np
    import Curve_Set_Points
    import PV_Inverter_Data
    [Volt_Var,Volt_Watt,Freq_Watt]=Curve_Set_Points.Curve_Set_Points()
    [Volt_Var_V,Volt_Var_Var]=Volt_Var
    [Volt_Watt_Volt,Volt_Watt_Watt]=Volt_Watt
    [dbUF,dbOF,kUF,kOF]=Freq_Watt
    [Efficiency,Vdc,DC_Power,Rating,F_P,F_Q,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
    [P_rated,P_min,S_max,Qmax_Plus,Qmax_Minus]=Rating
    
    
    if Auto_Direct_Mode==1:
        if Auto_Modes==1: #% Auto_Modes=1: frequency-watt
            if f<f_nom-dbUF:
                fw_P=np.minimum(P_Pre+P_rated*((f_nom-dbUF)-f)/f_nom/kUF,Pmpp_AC)
            elif f>f_nom+dbOF:
                fw_P=np.maximum(P_Pre-P_rated*(f-(f_nom+dbUF))/f_nom/kOF,P_min)
            else:
                fw_P=S_max*PF
            P=np.minimum(Pmpp_AC,fw_P)
            Q=P*np.sqrt(1-np.power(PF,2))/PF
        elif Auto_Modes==2: #% Auto_Modes=2:  Volt-watt
            f=interp1d(Volt_Watt_Volt,Volt_Watt_Watt)
            P=np.minimum(Pmpp_AC,f(V));
            Q=P*np.sqrt(1-np.power(PF,2))/PF
        elif Auto_Modes==3: #% Auto_Modes=3: power factor
            P=Pmpp_AC;
            Q=P*np.sqrt(1-np.power(PF,2))/PF# % Auto_Modes=4: volt-var 
        else:
            f=interp1d(Volt_Var_V,Volt_Var_Var)
            Q=f(V)
            P=Q*PF/np.sqrt(1-np.power(PF,2))
        
    #%% direct command mode    
    else:
        P=P_Direct
        Q=Q_Direct
    
    return P,Q