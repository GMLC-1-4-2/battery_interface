# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 09:38:01 2018

@author: rmahmud
"""

from datetime import datetime
from fleet_interface_PV import FleetInterface
PV=FleetInterface() #Battrey-equivalent interface for PV


#%%
"""PQ request"""
PQ_Req_PV=PV.process_request(ts=datetime.utcnow(),P_req=100,Q_req=0)# PV response for PQ request

#Printing PV Fleet response for PQ request
PQ_Req_PV_Disct=vars(PQ_Req_PV)
print('####### PQ Request response #######')
for keys in PQ_Req_PV_Disct:
    print(keys,'=',PQ_Req_PV_Disct[keys])
    
#%% 
"""Forecast request"""
Forecast_PV=PV.forecast([100,200])# PV response for Forecast request

#Printing PV Fleet response for Forecast request
Forecast_PV_Dict=vars(Forecast_PV)
print('\n\n####### Forecast #######')
for keys in Forecast_PV_Dict:
    print(keys,'=',Forecast_PV_Dict[keys])


