# -*- coding: utf-8 -*-
"""
Created on Mon July 20 2018
For GMLC 1.4.2, 
Testing the Fleet HVAC model

Last update: 08/06/2018
Version: 1.0

@author: dongj@ornl.gov
ORNL
"""

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import random

###############################################################################
from fridge_Cont_Fleet_ORNL import RFFleet


def main():
    Steps = 100 #num steps in simulation
    forecast = 1 # 0 is no, 1 is provide a forecast
    Q_request = 0 # reactive power request, not considering reactive power 
    Timestep = 0.5 #minutes
#    StartHr = 0 # hour of the month to start simulation
            

    ########################################################################
    #generate load request signal and regulation
#    NOTE: code is set up to deal with capacity separately from regulation, the only interface is in the capacity signal there is a single timestep
#    where regulation is called, the entire code switches into regulation mode for that single timestep (which is much longer than a regulation timestep)
#    when the calculations are complete, it returns conditions to be used for subsequent capacity timesteps
    P_request = []

    for step in range(Steps):
        capacity_needed = 10*6e3 + 1e3*random.random()#Watts needed, >0 is capacity add, <0 is capacity shed
#        magnitude_load_add_shed = capacity_needed/Fleet_size_represented #def magnitude of request for load add/shed
#        if step % 12 == 0 or step % 12 == 1 or step % 12 == 2: # this is my aribtrary but not random way of creating load add/shed events. should be replaced with a more realistic signal at some point
#            if step > 1:
#                s = -capacity_needed 
#            else:
##                service = ['none',0]
#                s=0
#        elif step % 7 == 0 or step % 7 == 1:
#            s = capacity_needed 
        s = 4 * capacity_needed * (np.sin(2*np.pi*(60*2/(10+step))))
        P_request.append(s)
#        fleet_load_request.append(service)

   
        # initializing fleet
    fleet = RFFleet(Steps, Timestep, P_request, Q_request, forecast)
    
    #calling fleet
    TotalServiceProvidedPerTimeStep, P_add_max, P_shed_max, P_injected, Q_injected, P_service, Q_service, P_service_max, Q_service_max, P_forecast, Q_forecast = fleet.ExecuteFleet(Steps, Timestep, P_request, Q_request, forecast)
    
    aTotalServiceProvidedPerTimeStep = np.array(TotalServiceProvidedPerTimeStep)
#    aP_service_max = np.array(P_service_max)
    
    
#    print(P_request)
#    print(aTotalServiceProvidedPerTimeStep) 
#    print(P_add_max)
#    print(P_shed_max)
   
        
    plt.figure(figsize = (12,8))
    plt.title('Ancillary service with 100 Commercial Refrigeration Units (negative means reduce)')
    plt.plot(aTotalServiceProvidedPerTimeStep, color = 'k', label = 'response')
    plt.plot(P_request, color = 'r', label = 'request')
    plt.grid()
    plt.legend()
    plt.xlabel('Time (10 min)', fontsize = 14, fontweight = 'bold')
    plt.ylabel('Power (W)', fontsize = 14, fontweight = 'bold')

       
if __name__ == '__main__':
    main()

    
