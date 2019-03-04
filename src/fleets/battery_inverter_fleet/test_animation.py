from datetime import datetime, timedelta
import numpy
#import sys
#from os.path import dirname, abspath
#sys.path.insert(0,dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from fleet_response import FleetResponse
from battery_inverter_fleet import BatteryInverterFleet
from grid_info import GridInfo
import matplotlib.pyplot as plt
import matplotlib.animation as animation 
import scipy.io as spio
import csv
import copy







def fleet_test(Fleet,fig,writer):
    
    mat = spio.loadmat('ERM_model_validation.mat', squeeze_me=True)
    t = mat['TT']
    P = -Fleet.num_of_devices* mat['PP']
    S = mat['SS']
    
    n = len(S)#len(t)

    t = t[numpy.arange(1000,n-1000,45)]
    P = P[numpy.arange(1000,n-1000,45)]
    S = S[numpy.arange(1000,n-1000,45)]


    n = len(t)
    print(n)
    Pach = numpy.zeros((n))
    Qach = numpy.zeros((n))
    f = numpy.zeros((n,2))
    v = numpy.zeros((n,2))
    SOC = numpy.zeros((n,Fleet.num_of_devices))
    #V = numpy.zeros(n)

    requests = []
    ts = datetime.utcnow()
    dt = timedelta(hours=(0.000277777778*45/3)) #hours
    for i in range(n):
        req = FleetRequest(ts=(ts+i*dt),sim_step=dt,p=P[i],q=None)
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
        P[i] = rsp.P_service """

    # process the requests 
    i = 0
    for req in requests[:n-10]:
        writer.grab_frame()
        Fleet.process_request(req)
        Pach[i] = sum(Fleet.P_service)
        Qach[i] = sum(Fleet.Q_service)
        """ f[i,0] = Grid.get_frequency(ts+i*dt,0)
        f[i,1] = Grid.get_frequency(ts+i*dt,1)
        v[i,0] = Grid.get_voltage(ts+i*dt,0)
        v[i,1] = Grid.get_voltage(ts+i*dt,1) """

        """ if v[i] < 100:
            print(str(100*i/n) + ' %') """
        if numpy.mod(i,numpy.floor(n/20)) == 0:
            print(str(100*i/n) + ' %')
        for j in range(Fleet.num_of_devices):
            SOC[i,j] = Fleet.soc[j] # show that process_request function updates the SoC
        #V[i] = Fleet.vbat
        i = i + 1
        fig.set_figheight(5)
        yield t, Pach, P, f, v, SOC, S*100, i

    """ plt.figure(1)
    plt.subplot(211)
    plt.plot(t[0:n], P[0:n], label='Power Requested')
    plt.plot(t[0:n], Pach, label='Power Achieved by Fleet')
    plt.xlabel('Time (hours)')
    plt.ylabel('Real Power (kW)')
    plt.legend(loc='lower right')
    plt.subplot(212)
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
    plt.show() """

def init():
    ax1.set_ylim(-200, 200)
    ax1.set_xlim(0, 24)
    ax2.set_ylim(0, 101)
    ax2.set_xlim(0, 24)
    del xdata[:]
    del ydata[:]
    line1.set_data(xdata, ydata)
    linet1.set_data(xdata, ydata)
    line2.set_data(xdata, ydata)
    line3.set_data(xdata, ydata)
    line4.set_data(xdata, ydata)
    linet2.set_data(xdata, ydata)
    line5.set_data(xdata, ydata)
    for linek in line6:
        linek.set_data(xdata, ydata) 
    return line1,line2,line3,line4,line5,line6, 

def run_animation1(data):
    # update the data
    t, Pach, P, f, v, SOC, S, j = data
    #plt.subplot(211)
    line1.set_data(t[j],P[j])
    linet1.set_data([t[j],t[j]],[-10,10])
    line2.set_data(t,P)
    line3.set_data([t[i] for i in range(j)],[Pach[i] for i in range(j)]) 

    return line1,linet1,line2,line3,

def run_animation2(data):
    # update the data
    t, Pach, P, f, v, SOC, S, j = data
    line4.set_data(t[j],S[j])
    linet2.set_data([t[j],t[j]],[0,101])
    line5.set_data(t,S)
    k = 0
    for linek in line6:
        linek.set_data([t[i] for i in range(j)],[SOC[i,k] for i in range(j)]) 
        k = k + 1

    return line4,linet2,line5,line6,


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
                    Power[T] = responses[T].P_service
                
                SoCFin = responses[n-1].soc  # get final SoC
                [P2, Cost, Able] = Fleet.cost(SoCFin, SoC0, del_t)  # calculate how much power it would take to return to SoC0
                
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
    Grid = GridInfo('Grid_Info_DATA_2.csv')
    Fleet = BatteryInverterFleet(Grid,'ERM')
    location = 0
    i = 0
    
    ts = datetime.utcnow()

    writer = animation.FFMpegFileWriter(fps=60)
    fig = plt.figure()
    fig.set_figheight(5)
    writer.setup(fig,'my_movie3-4.mp4',100)
    writer.saving(fig,'my_movie3-4.mp4',100) 

    data = fleet_test(Fleet,fig,writer)

    ax1 = plt.subplot(211)
    line1, = ax1.plot([], [], 'o', color='orange')
    linet1, = ax1.plot([], [], '--', lw=1, color='gray')
    line2, = ax1.plot([], [], '-', lw=2)
    line3, = ax1.plot([], [], '-', lw=2)
    ax1.set_ylim(-200, 200)
    ax1.set_xlim(0, 24)
    ax1.set_ylabel('Power (kW)')
    ani1 = animation.FuncAnimation(fig, run_animation1, data, blit=False, interval=10,
                              repeat=False, init_func=init)
    
    ax2 = plt.subplot(212)
    line4, = ax2.plot([], [], 'o', color='orange')
    linet2, = ax2.plot([], [], '--', lw=1, color='gray')
    line5, = ax2.plot([], [], '-', lw=2)
    line6 = ax2.plot([], [], '-', lw=2)
    for i in range(Fleet.num_of_devices-1):
        line6 = line6 + ax2.plot([], [], '-', lw=2)
    ax2.set_xlabel('Time (hours)')
    ax2.set_ylabel('State-of-Charge (%)')
    xdata, ydata = [], [] 
    
    ax2.set_ylim(0, 101)
    ax2.set_xlim(0, 24)
    ani2 = animation.FuncAnimation(fig, run_animation2, data, blit=False, interval=10,
                              repeat=False, init_func=init)
    

    plt.show()
    writer.finish()
    #Fleet.soc = 50.0*numpy.ones(Fleet.num_of_devices)
    #integration_test(Fleet)

