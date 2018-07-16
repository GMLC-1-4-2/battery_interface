import sys
from os.path import dirname, abspath
sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import scipy.io as spio
import csv
import copy
import numpy

from fleet_request import FleetRequest
from fleet_response import FleetResponse
from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet


def fleet_test(Fleet):
    
    mat = spio.loadmat('ERM_model_validation.mat', squeeze_me=True)
    t = mat['TT']
    P = -Fleet.num_of_devices* mat['PP']
    S = mat['SS']

    n = len(t)
    Pach = numpy.zeros((n))
    SOC = numpy.zeros((n,Fleet.num_of_devices))
    #V = numpy.zeros(n)

    requests = []
    ts = datetime.utcnow()
    
    dt = timedelta(hours=0.000092593) #hours
    for i in range(n):
        req = FleetRequest(ts=ts,sim_step=dt,p=P[i],q=0.0)
        requests.append(req)

    """ # print the initial SoC
    print("SoC =", str(Fleet.soc))
    FORCAST = Fleet.forecast(requests) # generate a forecast 
    print("SoC =", str(Fleet.soc))
    # make sure that the forecast function does not change the SoC
    """
    # print the forecasted achivable power schedule
    """ for i in range(n):
        rsp = FORCAST[i]
        P[i] = rsp.P_togrid """

    # process the requests 
    i = 0
    for req in requests:
        Fleet.process_request(req)
        Pach[i] = sum(Fleet.P_togrid)
        for j in range(Fleet.num_of_devices):
            SOC[i,j] = Fleet.soc[j] # show that process_request function updates the SoC
        #V[i] = Fleet.vbat
        i = i + 1

    plt.figure(1)
    plt.subplot(211)
    plt.plot(t[0:n], P[0:n], label='Power Requested')
    plt.plot(t[0:n], Pach, label='Power Achieved by Fleet')
    plt.xlabel('Time (hours)')
    plt.ylabel('Power')
    plt.legend(loc='lower right')
    plt.subplot(212)
    plt.plot(t[0:n],SOC, label='Simulated SoC')
    plt.plot(t[0:n],100*S[0:n], label='Recorded SoC')
    plt.xlabel('Time (hours)')
    plt.ylabel('State-of-Charge (%)')
    #plt.legend(loc='lower right')

    """ plt.figure(2)
    plt.plot(t, V) """
    plt.show()


def integration_test(Fleet):

    # Establish the test variables
    n = 24
    del_t = timedelta(hours=1.0)
    #dt = del_t.total_seconds()
    SoC0 = copy.copy(numpy.mean(Fleet.soc))
    #t = numpy.linspace(0, (n - 1), n)
    EffMatrix = numpy.zeros((n, n))
    ts = datetime.utcnow()
    print(n)

    for i in numpy.arange(0, n):
        print(i)
        if i == 1:
            print(i)
        for j in numpy.arange(0, n):
            if i != j:
                #Fleet = BatteryInverterFleet('config_ERM.ini')
                #Fleet.soc = SoC0  # initialize SoC
                Power = numpy.zeros(n)  # initialize Power
                Power[i] = Fleet.max_power_charge*Fleet.num_of_devices
                Power[j] = Fleet.max_power_discharge*Fleet.num_of_devices
                # simulate the system with SoC0 and Power requests
                requests = []
                for T in numpy.arange(0, n):
                    req = FleetRequest(ts,del_t,Power[T],0.0)
                    requests.append(req)
                    
                responses = Fleet.forecast(requests)

                for T in numpy.arange(0, n):
                    Power[T] = responses[T].P_togrid
                
                SoCFin = responses[n-1].soc  # get final SoC
                [P2, Cost, Able] = Fleet.cost(SoCFin, SoC0, del_t)  # retreeve how much power it would take to return to SoC0
                
                P2Charge = max(P2,0)
                P2Discharge = min(P2,0)
                if (Power[i] + P2Charge) != 0:
                    EffMatrix[i, j] = -(Power[j] +P2Discharge)/ (
                            Power[i] + P2Charge)  # calculate efficiency      DISCHARGE_ENERGY / CHARGE_ENERGY
                else:
                    EffMatrix[i, j] = 0
                if Able == 0:
                    EffMatrix[i, j] = 0

    print(EffMatrix)
    with open('EffMatrix.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerows(EffMatrix)           


if __name__ == '__main__':
    Fleet = BatteryInverterFleet('ERM')
    fleet_test(Fleet)
    Fleet.soc = 50.0*numpy.ones(Fleet.num_of_devices)
    integration_test(Fleet)

