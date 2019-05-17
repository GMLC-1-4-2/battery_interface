# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleets.fuel_cell_fleet.fuelcell_fleet import FuelCellFleet
from fleet_request import FleetRequest
from grid_info_artificial_inertia import GridInfo
from datetime import datetime, timedelta
from scipy.io import loadmat
from numpy import array
from matplotlib.pyplot import show, grid, subplots
if sys.version_info >= (3,6,7):
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
base_path = dirname(abspath(__file__))


def fleet_test1(fleet):
    p_data = loadmat(join(base_path, 'pdata.mat'), squeeze_me=True)

    # Power request
    p_req = p_data['PF']

    # Create fleet request
    fleet.is_autonomous = False
    fleet.FW21_Enabled = False
    fleet.is_P_priority = True
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts + i * dt), sim_step=dt, start_time=ts, p=v, q=0.) for i, v in
                     enumerate(p_req)]

    # Process the request
    P_togrid, Q_togrid, soc, P_service,  P_base, P_service_max, P_service_min, ts = [], [], [], [], [], [], [], []

    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        P_togrid.append(fleet_response.P_togrid)
        Q_togrid.append(fleet_response.Q_togrid)
        P_service.append(fleet_response.P_service)
        soc.append(fleet_response.E)
        P_base.append(fleet_response.P_base)
        P_service_max.append(fleet_response.P_service_max)
        P_service_min.append(fleet_response.P_service_min)
        ts.append(fleet_response.ts)

    # Generate the impact metrics file
    fleet.output_metrics('impact_metrics_%s' % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S')))

    # Plot the results
    fig1, y1 = subplots(figsize=(20, 12))
    y1.plot(ts, p_req, label='p_req')
    y1.plot(ts, P_service, label='P_service', alpha=0.5)
    y1.plot(ts, P_base, label='P_base')
    y1.set_ylabel('P(kW)')
    y1.set_xlabel('DateTime (mm-dd H:M:S)')
    y1.legend()
    grid()
    show()
    fig1.savefig(join(base_path, "FC_result_ALL_P_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                 bbox_inches='tight')

    kwargs = {'P_request': (p_req, 'kW'), 'P_togrid': (P_togrid, 'kW'),
              'P_service': (P_service, 'kW'), 'P_base': (P_base, 'kW'),
              'SoC': (soc, '%'),
              'P_service_max': (P_service_max, 'kW'),
              'P_service_min': (P_service_min, 'kW')}
    fleet.static_plots(**kwargs)

    fig1, y1 = subplots(figsize=(20, 12))
    p1, = y1.plot(ts, p_req, label='P_request')
    p2, = y1.plot(ts, P_togrid, label='P_togrid')
    p2a, = y1.plot(ts, P_service, label='P_service')
    y1.set_ylabel('P(kW)')
    y2 = y1.twinx()
    p3, = y2.plot(ts, array(soc)*1e2, label='SoC', color='g')
    y2.set_ylabel('SoC(%)')
    plots = [p1, p2, p2a, p3]
    y1.set_xlabel('DateTime (mm-dd H:M:S)')
    y1.legend(plots, [l.get_label() for l in plots])
    grid()
    show()
    fig1.savefig(join(base_path, "FC_result_All_Ps_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                 bbox_inches='tight')


def fleet_test2(fleet):

    # Create fleet request
    fleet.is_autonomous = True
    fleet.FW21_Enabled = True
    fleet.is_P_priority = False
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts + i * dt), sim_step=dt, start_time=ts, p=None, q=None) for i in
                     range(149)]

    # Process the request
    P_togrid, Q_togrid, soc, P_service,  P_base, P_service_max, P_service_min, ts, f = \
        [], [], [], [], [], [], [], [], []

    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        f.append(grid_dat.get_frequency(fr.ts_req, 0, fr.start_time))
        P_togrid.append(fleet_response.P_togrid)
        Q_togrid.append(fleet_response.Q_togrid)
        P_service.append(fleet_response.P_service)
        soc.append(fleet_response.E)
        P_base.append(fleet_response.P_base)
        P_service_max.append(fleet_response.P_service_max)
        P_service_min.append(fleet_response.P_service_min)
        ts.append(fleet_response.ts)
        print("P_togrid Rx", P_togrid[len(P_togrid)-1])
        print("P_service Rx", P_service[len(P_service) - 1])

    # Generate the impact metrics file
    fleet.output_metrics('impact_metrics_%s' % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S')))

    # Plot the results
    fig1, y1 = subplots(figsize=(20, 12))
    p1, = y1.plot(f, label='Frequency', color='g')
    y1.set_ylabel('Hz')
    y2 = y1.twinx()
    p2, = y2.plot(array(P_togrid)/240, label='P_togrid')
    y2.set_ylabel('Power Consumption (p.u.)')
    plots = [p1, p2]
    y1.set_xlabel('Time (s)')
    y1.legend(plots, [l.get_label() for l in plots])
    grid()
    show()
    fig1.savefig(join(base_path, "FC_result_P_grid_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                 bbox_inches='tight')

    fig2, y2 = subplots(figsize=(20, 12))
    y2.scatter(f, array(P_togrid)/240, label='P_togrid')
    y2.set_ylabel('Power Consumption(p.u.)')
    y2.set_xlabel('Hz')
    grid()
    show()
    fig2.savefig(join(base_path, "FC_result_P_service_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                 bbox_inches='tight')


if __name__ == '__main__':

    grid_dat = GridInfo('Grid_Info_data_artificial_inertia.csv')
    fleet = FuelCellFleet(grid_dat, "config.ini", "FuelCell")
    fleet_test2(fleet)


