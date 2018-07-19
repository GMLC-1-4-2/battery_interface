# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 15:54:25 2018

Example Higher Level Controller

@author: cbooten
"""
import random
#import numpy as np
#import os
import datetime
from fleet_request_2 import FleetRequest
from WH_fleet_control_6 import WaterHeaterFleet


def main():
    Steps = 10 #num steps in simulation
    if Steps > 1:
        forecast = 1
    else:
        forecast = 0
    Q_request = 0 # reactive power request, not considering reactive power 
    Timestep = 5 #minutes, NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 0.1, 0.2, 0.5, 1,2,3,4,5,6,10,12,15,20,30, 60, etc.
    starttime = 0 # 0-8759, hour of the year to start simulation
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
    FleetResponse = [[0]]*Steps
    
    for step in range(Steps):
        capacity_needed = 1e6 + 2e5*random.random()#Watts needed, >0 is capacity add, <0 is capacity shed
#        Fleet_size_represented = capacity_needed/4500 # approximately how many WH would be needed to be able to provide this capacity
#        magnitude_load_add_shed = capacity_needed/Fleet_size_represented #def magnitude of request for load add/shed
        if step % 12 == 0 or step % 12 == 1 or step % 12 == 2: # this is my aribtrary but not random way of creating load add/shed events. should be replaced with a more realistic signal at some point
            if step > 1:
                s = -capacity_needed 
            else:
#                service = ['none',0]
                s=0
        elif step % 7 == 0 or step % 7 == 1:
            s = capacity_needed 

        
        P_request.append(s)

############################################################################
#        Call fleet
    
        #creating service request object
        ServiceRequest = FleetRequest(StartTime, Timestep, P_request, Q_request, Steps, forecast) # ts,dt,Power[T],0.0)
    
        # initializing fleet
        fleet = WaterHeaterFleet(ServiceRequest)
        
        #calling fleet
        FleetResponse[step] = fleet.ExecuteFleet(ServiceRequest)

############################################################################
#   Plotting load add/shed responses
#    plt.figure(1)
#    plt.clf()
#    plt.plot(draw[0][0:20],'r*-',label = 'WH 1')
#    plt.plot(draw[1][0:20],'bs-',label = 'WH 2')
#    plt.plot(draw[2][0:20],'k<-',label = 'WH 3')
#    plt.ylabel('Water Draw [gal]')
#    plt.xlabel('step')
#    plt.legend()
#    plt.ylim([0,30])
#    
#    plt.figure(2)
#    plt.clf()
#    plt.plot(Ttank[0][0:50],'r*-',label = 'WH 1')
#    plt.plot(Ttank[1][0:50],'bs-',label = 'WH 2')
#    plt.plot(Ttank[2][0:50],'k<-',label = 'WH 3')
#    plt.ylabel('Ttank')
#    plt.xlabel('step')
#    plt.ylim([0,170])
#    plt.legend()
#    plt.show()
#    
#    plt.figure(3)
#    plt.clf()
#    plt.plot(ServiceCallsAccepted[0][0:20],'r*-',label = 'WH 1')
#    plt.plot(ServiceCallsAccepted[1][0:20],'bs-',label = 'WH 2')
#    plt.plot(ServiceCallsAccepted[2][0:20],'k<-',label = 'WH 3')
#    plt.ylabel('Service Calls Accepted - Not Inc. Regulation')
#    plt.xlabel('step')
#    plt.legend()
#    plt.show()
#
#    plt.figure(4)
#    plt.clf()
#    plt.plot(ServiceProvided[0][0:50],'r*-',label = 'WH 1')
#    plt.plot(ServiceProvided[1][0:50],'bs-',label = 'WH 2')
#    plt.plot(ServiceProvided[2][0:50],'k<-',label = 'WH 3')
#    plt.ylabel('Service Provided Per WH Per Timestep, W')
#    plt.xlabel('step')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(5)
#    plt.clf()
#    plt.plot(TotalServiceProvidedPerTimeStep[0:20],'r*-',label='Provided by Fleet')
#    plt.plot(fleet_load_request_total[0:20],'bs-', label ='Requested')
#    plt.ylabel('Total Service During Timestep, W')
#    plt.xlabel('step')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(7)
#    plt.clf()
#    plt.hist(TotalServiceCallsAcceptedPerWH)
#    plt.xlabel('Total Service Calls Accepted per WH Annually')
#    plt.show()
#        
#    plt.figure(9)
#    plt.clf()
#    plt.plot(AvailableCapacityAdd[0][0:20],'r*-',label='0')
#    plt.plot(AvailableCapacityAdd[1][0:20],'bs-',label='1')
#    plt.plot(AvailableCapacityAdd[2][0:20],'k<-',label='2')
#    plt.ylabel('Available Capacity for Load Add, W-hr')
#    plt.xlabel('step')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(10)
#    plt.clf()
#    plt.plot(AvailableCapacityShed[0][0:20],'r*-',label='0')
#    plt.plot(AvailableCapacityShed[1][0:20],'bs-',label='1')
#    plt.plot(AvailableCapacityShed[2][0:20],'k<-',label='2')
#    plt.ylabel('Available Capacity for Load Shed, W-hr')
#    plt.xlabel('step')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(19)
#    plt.clf()
#    plt.hist(TtankInitial)
#    plt.xlabel('Tank Temperature Initial [deg F]')
#    plt.show()
#    
#    plt.figure(20)
#    plt.clf()
#    plt.hist(TsetInitial)
#    plt.xlabel('Tank Setpoint Temperature Initial [deg F]')
#    plt.show()
#    
#    plt.figure(21)
#    plt.clf()
#    plt.hist(Capacity)
#    plt.xlabel('Tank Capacity [gal]')
#    plt.show()
#    
#    
#    ##########################################################################
#    #plotting regulation responses
#    plt.figure(11)
#    plt.clf()
#    plt.plot(TtankReg[0][0:20],'r*-',label = 'WH 1')
#    plt.plot(TtankReg[1][0:20],'bs-',label = 'WH 2')
#    plt.plot(TtankReg[2][0:20],'k<-',label = 'WH 3')
#    plt.ylabel('Tank Temperature deg F')
#    plt.xlabel('Regulation Timestep')
#    plt.legend()
#    plt.ylim([0,170])
#    
#    plt.figure(12)
#    plt.clf()
#    plt.plot(SoCReg[0][0:50],'r*-',label = 'WH 1')
#    plt.plot(SoCReg[1][0:50],'bs-',label = 'WH 2')
#    plt.plot(SoCReg[2][0:50],'k<-',label = 'WH 3')
#    plt.ylabel('SoC')
#    plt.xlabel('Regulation Timestep')
#    plt.ylim([-0.5,1.2])
#    plt.legend()
#    plt.show()
#    
#    plt.figure(13)
#    plt.clf()
#    plt.plot(ServiceCallsAcceptedReg[0][0:50],'r*-',label = 'WH 1')
#    plt.plot(ServiceCallsAcceptedReg[1][0:50],'bs-',label = 'WH 2')
#    plt.plot(ServiceCallsAcceptedReg[2][0:50],'k<-',label = 'WH 3')
#    plt.ylabel('Service Calls Accepted')
#    plt.xlabel('Regulation Timestep')
#    plt.legend()
#    plt.show()
#
#    plt.figure(14)
#    plt.clf()
#    plt.plot(ServiceProvidedReg[0][0:50],'r*-',label = 'WH 1')
#    plt.plot(ServiceProvidedReg[1][0:50],'bs-',label = 'WH 2')
#    plt.plot(ServiceProvidedReg[2][0:50],'k<-',label = 'WH 3')
#    plt.plot(ServiceProvidedReg[3][0:50],'go-',label = 'WH 4')
#    plt.ylabel('Service Provided Per WH Per Timestep, W')
#    plt.xlabel('Regulation Timestep')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(15)
#    plt.clf()
#    plt.plot(TotalServiceProvidedPerTimeStepReg[0:50],'r*-',label='Provided by Fleet')
#    plt.plot(fleet_regulation_request_magnitude[0:50],'bs-', label ='Requested')
#    plt.ylabel('Total Service During Timestep, W')
#    plt.xlabel('Regulation Timestep')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(16)
#    plt.clf()
#    plt.hist(TotalServiceCallsAcceptedPerWHReg)
#    plt.xlabel('Total Service Calls Accepted per WH Annually')
#    plt.show()
#
#    plt.figure(17)
#    plt.clf()
#    plt.plot(AvailableCapacityAddReg[0][0:50],'r*-',label='0')
#    plt.plot(AvailableCapacityAddReg[1][0:50],'bs-',label='1')
#    plt.plot(AvailableCapacityAddReg[2][0:50],'k<-',label='2')
#    plt.ylabel('Available Capacity for Load Add, W-hr')
#    plt.xlabel('Regulation Timestep')
#    plt.legend()
#    plt.show()
#    
#    plt.figure(18)
#    plt.clf()
#    plt.plot(AvailableCapacityShedReg[0][0:50],'r*-',label='0')
#    plt.plot(AvailableCapacityShedReg[1][0:50],'bs-',label='1')
#    plt.plot(AvailableCapacityShedReg[2][0:50],'k<-',label='2')
#    plt.ylabel('Available Capacity for Load Shed, W-hr')
#    plt.xlabel('Regulation Timestep')
#    plt.legend()
#    plt.show()





if __name__ == '__main__':
    main()
