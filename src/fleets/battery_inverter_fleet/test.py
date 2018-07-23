import sys
from datetime import datetime, timedelta
from os.path import dirname, abspath
import numpy
import scipy.io as spio
import matplotlib.pyplot as plt

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from fleet_response import FleetResponse
from battery_inverter_fleet import BatteryInverterFleet


def fleet_test():
    fleet = BatteryInverterFleet('config_CRM.ini')

    mat = spio.loadmat('ERM_model_validation.mat', squeeze_me=True)
    t = mat['TT']
    P = -fleet.num_of_devices* mat['PP']
    S = mat['SS']

    #n = len(t)
    n = 1000
    Pach = numpy.zeros((n))
    SOC = numpy.zeros((n,fleet.num_of_devices))
    #V = numpy.zeros(n)

    requests = []
    ts = datetime.utcnow()
    
    dt = timedelta(hours=0.000092593) #hours
    for i in range(n):
        req = FleetRequest(ts, dt, p=P[i], q=0.0)
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
        P[i] = rsp.P_injected """

    # process the requests 
    i = 0
    for req in requests:
        fleet.process_request(req)
        Pach[i] = sum(fleet.P_injected)
        for j in range(fleet.num_of_devices):
            SOC[i,j] = fleet.soc[j] # show that process_request function updates the SoC
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

def integration_test():

    # Establish the test variables
    n = 24
    dt = timedelta(hours=1)
    SoC0 = 50
    t = numpy.linspace(0, (n - 1), n)
    EffMatrix = numpy.zeros((n, n))
    ts = datetime.utcnow()
    print(n)

    for i in numpy.arange(0, n):
        for j in numpy.arange(0, n):
            if i != j:
                Fleet = BatteryInverterFleet('config_ERM.ini')
                Fleet.soc = SoC0  # initialize SoC
                Power = numpy.zeros(n)  # initialize Power
                Power[i] = Fleet.max_power_charge
                Power[j] = Fleet.max_power_discharge
                # simulate the system with SoC0 and Power requests
                for T in numpy.arange(0, n):
                    req = FleetRequest(ts,dt,Power[T],0.0)
                    Fleet.process_request(req)
                
                SoCFin = Fleet.soc  # get final SoC
                [P2, Cost, Able] = Fleet.cost(SoCFin, SoC0, dt)  # retreeve how much power it would take to return to SoC0
                P2Charge = max(P2,0)
                P2Discharge = min(P2,0)
                EffMatrix[i, j] = -(Power[j] +P2Discharge)/ (
                            Power[i] + P2Charge)  # calculate efficiency      DISCHARGE_ENERGY / CHARGE_ENERGY
                if P2<0:
                    print('err')
                if Able == 0:
                    EffMatrix[i, j] = 0

    print(EffMatrix)


if __name__ == '__main__':
    fleet_test()
    #integration_test()


