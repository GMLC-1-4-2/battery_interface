# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 16:12:09 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""

def SystemOperatorCommand():
    """Grid service dispatch instructions from system operator for Device fleet"""    


    T_Stamp=[2017,1,28,14,30,00]#Time stamp of the request
    Request='Forecast'
# Auto_Direct_Mode=1: Autonomous mode
# Auto_Direct_Mode=2:  direct command mode

    Auto_Direct_Mode=2
# Auto_Modes=1: frequency-watt
# Auto_Modes=2:  Volt-watt
# Auto_Modes=3: power factor
# Auto_Modes=4: volt-var 
    Auto_Modes=2
    PF=.9
    P_Direct=100e3
    Q_Direct=100e3
    Direct_Control=[P_Direct,Q_Direct,PF]
	#time response for P
    return Request,Auto_Direct_Mode,Auto_Modes,Direct_Control,T_Stamp