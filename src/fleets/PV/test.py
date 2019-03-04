# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 11:47:28 2018

@author: rmahmud
"""

import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from datetime import datetime, timedelta
import numpy
import matplotlib.pyplot as plt
import scipy.io as spio

from fleet_request import FleetRequest
from grid_info import GridInfo
from fleets.PV.PV_Inverter_Fleet import PVInverterFleet


def fleet_test(Fleet,Grid):
    mat = spio.loadmat('ERM_model_validation.mat', squeeze_me=True)
    t = mat['TT']
    P = Fleet.num_of_devices* mat['PP']
 
    Op_Mode=4 # Op_Mode=1 : Volt-Var
        # Op_Mode=2 : Frequency-watt
        # Op_Mode=3 : process request
        # Op_Mode=4 : Forecast

    n = 8000#len(t)
    Pach = numpy.zeros((n))
    Qach = numpy.zeros((n))
    f = numpy.zeros((n,2))
    v = numpy.zeros((n,2))
    
    requests = []
    ts = datetime.utcnow()
    dt = timedelta(hours=0.000277777778) #hours
    for i in range(n):
        req = FleetRequest(ts=(ts+i*dt),sim_step=dt,p=P[i],q=None)
        requests.append(req)
        
    i = 0
    
    
    if Op_Mode==1:
        for i in range(n):
            res=Fleet.Volt_Var(ts=(ts+i*dt))
            Pach[i] = res.P_togrid
            Qach[i] = res.Q_togrid
            f[i,0] = Grid.get_frequency(ts+i*dt,0)
            f[i,1] = Grid.get_frequency(ts+i*dt,1)
            v[i,0] = Grid.get_voltage(ts+i*dt,0)
            v[i,1] = Grid.get_voltage(ts+i*dt,1)
            
            if numpy.mod(i,10000) == 0:
                print(str(100*i/n) + ' %')
           
            #V[i] = Fleet.vbat
            i = i + 1
    elif Op_Mode==2:
        for i in range(n):
            res=Fleet.frequency_watt(ts=(ts+i*dt))
            Pach[i] = res.P_togrid
            Qach[i] = res.Q_togrid
            f[i,0] = Grid.get_frequency(ts+i*dt,0)
            f[i,1] = Grid.get_frequency(ts+i*dt,1)
            v[i,0] = Grid.get_voltage(ts+i*dt,0)
            v[i,1] = Grid.get_voltage(ts+i*dt,1)
            
            if numpy.mod(i,10000) == 0:
                print(str(100*i/n) + ' %')
           
            #V[i] = Fleet.vbat
            i = i + 1
    elif Op_Mode==3:
        for req in requests:
            res=Fleet.process_request(req)
            Pach[i] = res.P_togrid
            Qach[i] = res.Q_togrid
            f[i,0] = Grid.get_frequency(ts+i*dt,0)
            f[i,1] = Grid.get_frequency(ts+i*dt,1)
            v[i,0] = Grid.get_voltage(ts+i*dt,0)
            v[i,1] = Grid.get_voltage(ts+i*dt,1)
            
            if numpy.mod(i,10000) == 0:
                print(str(100*i/n) + ' %')
           
            #V[i] = Fleet.vbat
            i = i + 1
    else:
        for req in requests:
            res=Fleet.forecast(req)
            print(res.P_togrid_max)
            Pach[i] = res.P_togrid_max
            Qach[i] = res.Q_togrid_max
            f[i,0] = Grid.get_frequency(ts+i*dt,0)
            f[i,1] = Grid.get_frequency(ts+i*dt,1)
            v[i,0] = Grid.get_voltage(ts+i*dt,0)
            v[i,1] = Grid.get_voltage(ts+i*dt,1)
            
            if numpy.mod(i,10000) == 0:
                print(str(100*i/n) + ' %')
           
            #V[i] = Fleet.vbat
            i = i + 1
        
            
    if Op_Mode!=4:        
        plt.figure(1)
        plt.subplot(211)
        plt.plot(t[0:n], P[0:n], label='Power Requested')
        plt.plot(t[0:n], Pach, label='Power Achieved by Fleet')
        plt.xlabel('Time (hours)')
        plt.ylabel('Real Power (kW)')
        plt.legend(loc='lower right')
        plt.subplot(212)
        plt.plot(t[0:n],60.036*numpy.ones(n))
        plt.plot(t[0:n],59.964*numpy.ones(n))
        plt.plot(t[0:n],f[0:n,0], label='Grid Frequency')
        #plt.plot(t[0:n],100*S[0:n], label='Recorded SoC')
        plt.xlabel('Time (hours)')
        plt.ylabel('frequency (Hz)')
        #plt.legend(loc='lower right')
    
        plt.figure(2)
        plt.subplot(211)
        plt.plot(t[0:n], Qach, label='Reactive Power Achieved by Fleet')
        plt.ylabel('Reactive Power (kvar)')
        plt.legend(loc='lower right')
        plt.subplot(212)
        plt.plot(t[0:n], v[0:n,0], label='Voltage at location 1')
        plt.plot(t[0:n], v[0:n,1], label='Voltage at location 2')
        plt.xlabel('Time (hours)')
        plt.ylabel('Voltage (V)')
        plt.legend(loc='lower right')
        plt.show()
    else:
        plt.figure(1)
        plt.plot(t[0:n], Pach, label='Power Achieved by Fleet')
        plt.xlabel('Time (hours)')
        plt.ylabel('Real Power (kW)')
        plt.legend(loc='lower right')
        #plt.legend(loc='lower right')
    
        plt.figure(2)
        plt.subplot(211)
        plt.plot(t[0:n], Qach, label='Reactive Power Achieved by Fleet')
        plt.ylabel('Reactive Power (kvar)')
        plt.legend(loc='lower right')
        plt.show()
        

if __name__ == '__main__':
    location = 0
    i = 0
    Grid = GridInfo('Grid_Info_DATA_2.csv')
    Fleet = PVInverterFleet(GridInfo=Grid)
    ts = datetime.utcnow()

    fleet_test(Fleet,Grid)
