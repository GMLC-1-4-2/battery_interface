# -*- coding: utf-8 -*-
"""
Last updated on Thursday Jul 26 2018

Example Higher Level Controller

@author: Chuck Booten (NREL), Jeff Maguire (NREL)
    
"""
import random
import numpy as np
import os
import datetime
import matplotlib.pyplot as plt
from fleet_request import FleetRequest
from WH_fleet_control import WaterHeaterFleet

def main():
    
    #Test case: Run a forecast for the day of July 26th
    #Configure the simulation to be run. Need to set the number of timesteps, start time, and the length of the timestep (in minutes)
    Steps = 24 #num steps in simulation, if greater than 1 assuming a forecast is being requested
    Timestep = 60 #minutes, NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 0.1, 0.2, 0.5, 1,2,3,4,5,6,10,12,15,20,30, 60, etc.
    allowable_timesteps = [0.1, 0.2, 0.5, 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
    if Timestep not in allowable_timesteps:
        print("Timestep must be a divisor of 60")
        return
    starttime = 206*24 # 0-8759, hour of the year to start simulation
    if Steps > 1:
        forecast = 1
    else:
        forecast = 0
    Q_request = 0 # reactive power request, water heater can't provide reactive power
    Timestep = datetime.timedelta(minutes=Timestep)
    startday = (starttime // 24) + 1
    monthindex = [[1,31],[2,59],[3,90],[4,120],[5,151],[6,181],[7,212],[8,243],[9,273],[10,304],[11,334],[12,365]] #doesn't account for leap years
    for m in monthindex:
        if startday <= m[1]:
            startmonth = m[0]
            break
    
    if startmonth > 1:
        startday -= monthindex[(m[0]-2)][1]

    starthour = starttime % 24
    
    StartTime = datetime.datetime(2018,startmonth,startday,starthour)         

    ########################################################################
    #generate load request signal and regulation
#    NOTE: code is set up to deal with capacity separately from regulation, the only interface is in the capacity signal there is a single timestep
#    where regulation is called, the entire code switches into regulation mode for that single timestep (which is much longer than a regulation timestep)
#    when the calculations are complete, it returns conditions to be used for subsequent capacity timesteps
    P_request = []
    FleetResponse = [0]
    
    for step in range(Steps):
        capacity_needed = 1e6
#        capacity_needed = 1e6 + 2e5*random.random()#Watts needed, >0 is capacity add, <0 is capacity shed
#        Fleet_size_represented = capacity_needed/4500 # approximately how many WH would be needed to be able to provide this capacity
#        magnitude_load_add_shed = capacity_needed/Fleet_size_represented #def magnitude of request for load add/shed
        if step % 12 == 0 or step % 12 == 1 or step % 12 == 2: # this is my aribtrary but not random way of creating load add/shed events. should be replaced with a more realistic signal at some point
            if step > 1:
                s = -capacity_needed 
            else:
#                service = ['none',0]
                s = 0
        elif step % 7 == 0 or step % 7 == 1:
            s = capacity_needed 
        else:
            s = 0

        P_request.append(s)

############################################################################
#        Call fleet
    
    #creating service request object
    ServiceRequest = FleetRequest(StartTime, Timestep, P_request, Q_request, Steps, forecast) # ts,dt,Power[T],0.0)

    # initializing fleet
    fleet = WaterHeaterFleet()
    
    #calling fleet
    FleetResponse = fleet.process_request(ServiceRequest)
    
    #Gather data to plot and look at the results
    #for y in range FleetResponse[0].AvailableCapacityAdd:
        
    #for x in range(len(FleetResponse)):
    #    for y in range FleetResponse[0].AvailableCapacityAdd:
    a=1
############################################################################
    #Plotting load add/shed responses
    '''
    for n in range(len(FleetResponse.IsAvailableAdd)):
        plt.figure(n+1)
        plt.clf()
        plt.plot(FleetResponse.IsAvailableAdd[n],'r*-',label = 'AvailAdd')
        plt.plot(FleetResponse.IsAvailableShed[n],'bs-',label = 'AvailShed')
        plt.ylabel('Availability')
        plt.xlabel('step')
        plt.title('Water Heater {} Availability'.format(n+1))
        plt.legend()
        plt.ylim([-1,2])
    plt.show()
    
    for n in range(len(FleetResponse.IsAvailableAdd)):
        plt.figure(n+1)
        plt.clf()
        plt.plot(FleetResponse.Tset[n],'r*-',label = 'Tset')
        plt.plot(FleetResponse.Ttank[n],'bs-',label = 'Ttank')
        plt.ylabel('Temperature (F)')
        plt.xlabel('step')
        plt.title('Water Heater {} Setpoint and tank temperature'.format(n+1))
        plt.legend()
        plt.ylim([100,160])
    plt.show()
    
    for n in range(len(FleetResponse.IsAvailableAdd)):
        plt.figure(n+1)
        plt.clf()
        plt.plot(FleetResponse.IsAvailableAdd[n],'r*-',label = 'AvailAdd')
        plt.plot(FleetResponse.IsAvailableShed[n],'bs-',label = 'AvailShed')
        plt.ylabel('Availability')
        plt.xlabel('step')
        plt.title('Water Heater {} Availability'.format(n+1))
        plt.legend()
        plt.ylim([-1,2])
    plt.show()
    '''
if __name__ == '__main__':
    main()
