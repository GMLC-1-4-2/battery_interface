# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 15:58:19 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""


import SystemOperatorCommand
import PV_Fleet
from BEM import BEM_Param
from matplotlib import pyplot as plt
import numpy as np

Fleet_PV=PV_Fleet.Fleet(SystemOperatorCommand)
Request=SystemOperatorCommand.SystemOperatorCommand()[0]

#Fleet_PV=BEM_Param('PV') #Battery equivalent model parameters for PV Fleet --> variable assignment


# takes operation command from system operator and updates the system operator 
# about operation status of PV fleet



# %%Plots


# Plot Active power
#f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=True)
if Request=='Forecast':
    plt.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Fleet_PV.P_Max])
    plt.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Fleet_PV.Q_Max_Plus],'r')
    plt.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Fleet_PV.Q_Max_Minus],'r')
    plt.legend(['Active Power (MW)','Reactive Power_Plus (MVAR)','Reactive Power_Minus (MVAR)'])
    plt.ylabel('Power')
    plt.xlabel('Time (Hr)')
    
else:
    print('P_Max: %g' %(Fleet_PV.P_Max/1e6))
    print('P_Requested: %g' %(Fleet_PV.P_Requested/1e6))
#    print('P_Grid: %g' %(Fleet_PV.P_Grid/1e3))
    
    #print('Q_Max: %g' %(Fleet_PV.Q_Max_Plus/1e6))
    #print('Q_Requested: %g' %(Fleet_PV.Q_Requested/1e6))
    #print('Q_Grid: %g' %(Fleet_PV.Q_Grid/1e6))
    dummy=np.ones(len(Fleet_PV.Time_Steps))
    P_Requested_MW=[Fleet_PV.P_Requested*x/1e6 for x in dummy]
    P_Grid_MW=[x/1e6 for x in Fleet_PV.P_Grid]
    plt.plot(Fleet_PV.Time_Steps,P_Grid_MW,Fleet_PV.Time_Steps,P_Requested_MW,'r')
    plt.legend(['P_Grid','P_Requested'])
    plt.ylabel('MW')
    plt.xlabel('Time (hr)')
    
    #plt.plot(Fleet_PV.Time_Steps,)
#ax1.set_title('Active Power (MW)')
#ax2.plot(Fleet_PV.Time_Steps, [x/1e6 for x in P_Requested])
#ax2.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Fleet_PV.P_Grid], color='r')
#ax2.set_xlabel('Time (hr)')
#ax2.set_ylabel('Power')
#ax1.legend(['P avaiable'])
#a#x2.legend(['P requested'])
#ax2.legend(['P to grid'])
# Fine-tune figure; make subplots close to each other and hide x ticks for
# all but bottom plot.
#f.subplots_adjust(hspace=0)
#plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)

#Plot reactive power
#f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=True)
#ax1.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Fleet_PV.Q_Max_Plus])
#ax1.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Fleet_PV.Q_Max_Minus])
#ax1.set_title('Rective Power (MVar)')
#ax2.plot(Fleet_PV.Time_Steps, [x/1e6 for x in Q_Requested])
#ax3.plot(Time_steps, [x/1e6 for x in Fleet_PV.Q_Grid], color='r')
#ax2.set_xlabel('Time (hr)')
#ax2.set_ylabel('Power')
# Fine-tune figure; make subplots close to each other and hide x ticks for
# all but bottom plot.
#f.subplots_adjust(hspace=0)
#plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
#ax1.legend(['Q avaiable'])
#ax2.legend(['Q requested'])
#ax2.legend(['Q to grid'])


    
    #fig, ax1 = plt.subplots()
    #ax1.plot(Time_, G_rec, 'b-',[],[])
    #ax1.set_xlabel('Time (Hr)')
         #Make the y-axis label, ticks and tick labels match the line color.
    #ax1.set_ylabel('Irr', color='b')
    #ax1.tick_params('y', colors='b')
    #ax2 = ax1.twinx()
    #ax2.plot(Time_,T_rec, 'r')
    #ax2.set_ylabel('Temperature ($^0$C)', color='r')
    #ax2.tick_params('y', colors='r')