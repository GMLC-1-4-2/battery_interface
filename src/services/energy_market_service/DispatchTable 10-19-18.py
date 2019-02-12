"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Copyright (c) 2018, Lawrence Livermore National Security, LLC. 
Produced at the Lawrence Livermore National Laboratory 
Written by Thomas Edmunds, edmunds2@llnl.gov. 
LLNL-CODE-755518. 
All rights reserved. 
 

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Dispatch algorithm for grid services
Tom Edmunds edmunds2@llnl.gov  925-423-8982

Read device round trip efficincy (eff), ISO energy price (price), elasticity (strike),
and charge state at midnight (charge[0]). Compute optimal value for pairs of 
charge-discharge timesteps [i,j].
 -*- coding: utf-8 -*-
"""

import numpy as np
import matplotlib.pyplot as plt
import csv
#from numba import jit
#from numpy import arange


#Constants
INF = 999999
timesteps = 288
nChg = 3  #Number of timesteps required to charge or discharge (< timesteps/2)
tFull = 500 #Time when system must have full charge

# Read data from csv files

# Read prices
price = np.genfromtxt('CAISO Apr 2016.csv', delimiter = ',' )
#print('Prices (price):', price) 

#
"""
Read round trip eff and strike for pairs of charge & discharge hours
eff and strike are square matrices of dimensions [timesteps, timesteps]
elements on diagonal and above are for charge in timestep i and discharge in j
elements below the diagonal are for dicharge in timestep i and charge in j
"""
eff = np.genfromtxt('Round trip efficiency.csv', delimiter = ',' )
#print('Round trip efficiency (eff):', eff)

#Read charge state - for this implementation just use state at period 0
charged = np.genfromtxt('Charge state off.csv', delimiter = ',' )
#print('Charge state:', charged)

# Read price elasitity (strike price) file
strike = np.genfromtxt('Strike price.csv', delimiter = ',' )
#print('Strike:', strike)

# Construct profit table: profit = -price(charge) + eff(i,j)*price(discharge)
# Fill profit matrix with NaNs
profit = np.full([timesteps, timesteps], np.nan)
#
"""
Profit depends upon order of charge and discharge 
if charge period i < discharge period j it must be discharged at midnight 
if charge period i > discharge period j it must be charged at midnight
"""

for i in range(timesteps):
    for j in range(timesteps):
        profit[i,j] = -price[i] + eff[i,j]*price[j]
        #print(i, j, profit[i,j], price[i], eff[i,j])

# Construct value table: value = profit - strike(i,j)
value = np.full([timesteps, timesteps], np.nan)
for i in range(timesteps):
    for j in range(timesteps):
        value[i,j] = profit[i,j] - strike[i,j]
        #print(i, j, profit[i,j], strike[i,j], value[i,j])

def plotCurve(curve, title, xLabel, yLabel): 
    hour = range(timesteps)
    plt.plot(hour, curve, label = title)
    plt.legend()
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.grid(b=True, which='both')
    plt.show()

def plotHeatMap(matrix, xLabel, yLabel, scaleLabel):
    import matplotlib.cm as cm
    #cmap = cm.get_cmap('nipy_spectral_r')
    #cmap = cm.get_cmap('plasma_r')
    cmap = cm.get_cmap('RdYlGn')
    nx,ny = np.shape(matrix)
    cs = plt.pcolor(matrix, cmap=cmap)
    cb = plt.colorbar(cs,orientation = 'vertical')
    cb.set_label(scaleLabel)
    plt.xlim(0,nx)
    plt.ylim(0,ny)
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.grid(True)
    plt.show()
    return

def oneCycleNPer(INF, nChg, value, startT, stopT, tFull):
# One daily cycle with nChg period contiguous charge and discharge times
# Array indexs first period of chorge or discharge event
    nDim = stopT - startT
    print('nDim = ', nDim)
    #Dimension matrices and fill with NANs
    nProfit = np.full([nDim, nDim], np.nan)
    nValue = np.full([nDim, nDim], np.nan)
    # Compute profit array for charge period and discharge period lagged by nChg
    # or more time periods
    
    if charged[startT] == 0:     # Discharged at start of period 
        for i in range(nDim - 2*nChg + 2):
            for j in range (i + nChg, nDim - nChg + 2):
                nProfit[i, j] = profit[startT + i, startT + j]
                nValue[i, j] = value[startT + i, startT + j]
                for k in range(1, nChg): 
                    nProfit[i, j] = nProfit[i , j] + profit[startT + i + k, startT + j + k] 
                    nValue[i, j] = nValue[i, j] + value[startT + i + k, startT + j + k]
                #Test to see if charge too late, after time tFull
                if i > (tFull - nChg):
                    nValue[i,j] = - INF
                #Test to see if charged then discharged before time tFull
                if j > tFull - nChg:
                    nValue[i,j] = - INF
        # Find charge-discharge hours with maximum value for single cycle
        maxValue = -INF
        for i in range(nDim):
            for j in range(i + nChg, nDim - nChg + 1):
                if nValue[i,j] > maxValue:
                    maxValue = nValue[i,j]
                    chargeMax = i
                    dischargeMax = j
        charged[stopT] = 1
    else:   # Charged at start of period (just change i and j indices in loops)
        for j in range(nDim - 2*nChg + 2):
            for i in range (j + nChg, nDim - nChg + 2):
                nProfit[i, j] = profit[startT + i, startT + j]
                nValue[i, j] = value[startT + i, startT + j]
                for k in range(1, nChg): 
                    nProfit[i, j] = nProfit[i , j] + profit[startT + i + k, startT + j + k] 
                    nValue[i, j] = nValue[i, j] + value[startT + i + k, startT + j + k]
                #Test to see if discharged before time tFull and charged after time tFull
                if j > tFull:
                    if i > (tFull - nChg):
                        nValue[i,j] = - INF
        # Find charge-discharge hours with maximum value for single cycle
        maxValue = -INF
        for j in range(nDim):
            for i in range(j + nChg, nDim - nChg + 1):
                if nValue[i,j] > maxValue:
                    maxValue = nValue[i,j]
                    chargeMax = i
                    dischargeMax = j
        charged[stopT] = 1
    return(chargeMax + startT, dischargeMax + startT, maxValue, charged[stopT])
    
plotCurve(price, 'CAISO Price Mar 2016', 'time', '$/MWh')
plotHeatMap(eff, 'Discharge time', 'Charge time', 'Round Trip efficiency (%)')
plotHeatMap(strike, 'Discharge time', 'Charge time', 'Strike price-elasticity ($/MWh)')
plotHeatMap(profit, 'Discharge time', 'Charge time', 'Energy arbitrage profit ($/MWh)')
plotHeatMap(value, 'Discharge time', 'Charge time', 'Value = Profit - Strike price ($/MWh)')

#Call oneCycleNPer for single daily cycle
startT = 0
stopT = timesteps - 1
chargeMax, dischargeMax, maxValue, charged[stopT] = oneCycleNPer(INF, nChg, value, startT, stopT, tFull)
print('startT = ', startT, 'stopT = ', stopT)
print('Charge state at beginning of period = ', charged[startT] )
print('Charge state at end of period = ', charged[stopT] )
print('Solution for single daily cycle ', nChg, 'timesteps to charge')
print('Max value = ', maxValue, '$/MWh')
print('Charge time = ', chargeMax)
print('Discharge time = ', dischargeMax)
print()


# Write dispatch orders for single daily cycle to file 
dispatch = open('dispatchOrders.csv', 'a')
header = ['Single cycle output:, timesteps, startT, stopT, charged[startT], nChg, tFull, maxValue, chargeMax, dischargeMax \n']
dispatch.writelines( header )
data = [str(timesteps), '\n', str(startT), '\n', str(stopT), '\n', str(charged[startT]), '\n', 
        str(nChg), '\n', str(tFull), '\n', str(maxValue), '\n', str(chargeMax), '\n', str(dischargeMax), '\n']
dispatch.writelines( data )



#Call oneCycleNPer twice for the day
#Call oneCycleNPer for first cycle
startT = 0
stopT = int(timesteps/2) - 1
chargeMax, dischargeMax, maxValue, charged[stopT] = oneCycleNPer(INF, nChg, value, startT, stopT, tFull)
print('startT = ', startT, 'stopT = ', stopT)
print('Charge state at beginning of period = ', charged[startT] )
print('Charge state at end of period = ', charged[stopT] )
print('Solution for single cycle ', nChg, 'timesteps to charge')
print('Max value = ', maxValue, '$/MWh')
print('Charge time = ', chargeMax)
print('Discharge time = ', dischargeMax)
print()

# Write dispatch orders for first cycle to file 
dispatch = open('dispatchOrders.csv', 'a')
header = ['First cycle output:, timesteps, startT, stopT, charged[startT], nChg, tFull, maxValue, chargeMax, dischargeMax \n']
dispatch.writelines( header )
data = [str(timesteps), '\n', str(startT), '\n', str(stopT), '\n', str(charged[startT]), '\n', 
        str(nChg), '\n', str(tFull), '\n', str(maxValue), '\n', str(chargeMax), '\n', str(dischargeMax), '\n']
dispatch.writelines( data )

#Call oneCycleNPer for second cycle
startT = int(timesteps/2)
#Charge state at beginning of period = charge state from previous period
charged[startT] = charged[stopT]
stopT = timesteps - 1
chargeMax, dischargeMax, maxValue, charged[stopT] = oneCycleNPer(INF, nChg, value, startT, stopT, tFull)
print('startT = ', startT, 'stopT = ', stopT)
print('Charge state at beginning of period = ', charged[startT] )
print('Charge state at end of period = ', charged[stopT] )
print('Solution for single cycle ', nChg, 'timesteps to charge')
print('Max value = ', maxValue, '$/MWh')
print('Charge time = ', chargeMax)
print('Discharge time = ', dischargeMax)
print()

# Write dispatch orders for second cycle to file 
dispatch = open('dispatchOrders.csv', 'a')
header = ['Second cycle output:, timesteps, startT, stopT, charged[startT], nChg, tFull, maxValue, chargeMax, dischargeMax \n']
dispatch.writelines( header )
data = [str(timesteps), '\n', str(startT), '\n', str(stopT), '\n', str(charged[startT]), '\n', 
        str(nChg), '\n', str(tFull), '\n', str(maxValue), '\n', str(chargeMax), '\n', str(dischargeMax), '\n']
dispatch.writelines( data )
dispatch.close()

#Phase 1.1: 
#Make data files to illustate 5 minute dispatch. Include some structure like varying 
# round trip efficiwency and strike prices to reflect consumer behavior such as 
# no discharge before morning or evening consumer demands for hot water or PEV readiness

#Phase 2:  
#Build API to interface with devices - get round trip efficiency and charge time, 
# and return dispatch orders

#Phase 3: 
#Build mixed integer optimization model with parameters specified by 
# device modelers and interface to open source MIP solver
# Allow non-integer charge state at time 0
# Allow rolling horizon

#Phase 4:
#Interface MIP solution with devices



