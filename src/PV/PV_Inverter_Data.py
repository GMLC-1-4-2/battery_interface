# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 13:41:32 2018

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def ABB_MICRO_025():
    import numpy as np
    from scipy import signal
    
    #inverter rating
    Qmax_Plus=80
    Qmax_minus=80
    P_rated=250
    P_min=0
    S_max=250
    Rating=[P_rated,P_min,S_max,Qmax_Plus,Qmax_minus]
    
    
    #Time response
    wn_P=4.4
    tau_delay_P=0.0005
    a_P=1
    Zeta_P=0.4
    num=[wn_P*wn_P]
    den=[a_P, 2*Zeta_P*wn_P, wn_P*wn_P]
    F_P=signal.TransferFunction(num, den)
    
    F_Q=signal.TransferFunction(num, den)
    #F_P=tf(num,den)
    
    P_Ramp_UP=1.0#Ramp rate real power up
    P_Ramp_Down=1.0#Ramp rate real power down
    Q_Ramp_UP=1.0#Ramp rate reactive power up
    Q_Ramp_Down=1.0#Ramp rate reactive power down
    
    Ramp_Limit=[P_Ramp_UP,P_Ramp_Down,Q_Ramp_UP,Q_Ramp_Down]
    
    
    
    Efficiency = np.array([[91.2,94.5,95.4,96,96.2,96.2],
                           [91.5,94.4,95.5,96.2,96.3,96.4],
                           [91.2,94.3,95.3,96.2,96.2,96.4]])
    AC_Power=np.array([25, 50, 75, 125, 187.5, 250])
    Vdc=np.array([30, 40, 50])
     
    a=[]
    for x in range(3):
        a.append(AC_Power)
        
    DC_Power=np.divide(a,Efficiency/100)
    
    return Efficiency,Vdc,DC_Power,Rating,F_P,F_Q,Ramp_Limit