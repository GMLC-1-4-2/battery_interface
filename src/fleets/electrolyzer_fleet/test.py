# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleets.electrolyzer_fleet.ey_fleet import ElectrolyzerFleet, static_plots
from fleet_request import FleetRequest
from datetime import datetime, timedelta
from scipy.io import loadmat
base_path = dirname(abspath(__file__))


def fleet_test1(fleet):

    """
    SCENARIO 1: Pre-load the power request curve
    Number of electrolyzers (Ne) automatically computed based on the
    area of the power request curve
    """
    # Set p_req as None in the model
    # Get simulation duration based on pre-loaded power curve data
    n = fleet.timespan

    # Create fleet request
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts+i*dt), sim_step=dt, p=None, q=None) for i in range(n)]

    # Process the request
    p_resp, q_resp, soc, ne, nf, V, Ir, status, fleetsize = [], [], [], [], [], [], [], [], []
    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        p_resp.append(fleet_response.P_togrid)
        q_resp.append(fleet_response.Q_togrid)
        soc.append(fleet_response.soc)
        ne.append(fleet_response.ne)
        nf.append(fleet_response.nf)
        V.append(fleet_response.V)
        Ir.append(fleet_response.Ir)
        status.append(fleet_response.status)
        fleetsize.append(fleet_response.ey_fleet)

    # Simulation results
    stat = "fully charged at %s sec." % str(sum(status))

    # Plot the results
    kwargs = {'P_response': (p_resp, 'kW'),
              'Q_request': (q_resp, 'kVAr'), 'SoC ('+stat+')': (soc, '%'),
              'Faraday Efficiency': (nf, '%'), 'Energy efficiency of a cell': (ne, '%'),
              'V': (V, 'Volts'), 'Ir': (Ir, 'Amps'),
              'Fleet Availability: %s' % fleetsize[0]: (fleetsize, 'Fleets')}
    static_plots(**kwargs)


def fleet_test2(fleet):
    """
    SCENARIO 2: Use instantaneous power request
    """
    p_data = loadmat(join(base_path, 'pdata.mat'), squeeze_me=True)
    time = p_data['TT']

    # Power direction wrt the Grid.
    # Ey is negative power
    p_req = p_data['PP']

    # base load of 20% of initial power requirement
    bload = p_req[0]*0.2
    p_curve = [bload if v < 0 else abs(v)-bload for _, v in enumerate(p_req)]

    # Create fleet request
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts+i*dt), sim_step=dt, p=v, q=None) for i, v in enumerate(p_curve)]

    # Process the request
    p_resp, q_resp, soc, ne, nf, V, Ir, status, fleetsize = [], [], [], [], [], [], [], [], []
    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        p_resp.append(fleet_response.P_togrid)
        q_resp.append(fleet_response.Q_togrid)
        soc.append(fleet_response.soc)
        ne.append(fleet_response.ne)
        nf.append(fleet_response.nf)
        V.append(fleet_response.V)
        Ir.append(fleet_response.Ir)
        status.append(fleet_response.status)
        fleetsize.append(fleet_response.ey_fleet)

    # Simulation results
    stat = "fully charged at %s sec." % str(sum(status))

    # Plot the results
    kwargs = {'P_request': (p_curve, 'kW'), 'P_response': (p_resp, 'kW'),
              'Q_request': (q_resp, 'kVAr'), 'SoC ('+stat+')': (soc, '%'),
              'Faraday Efficiency': (nf, '%'), 'Energy efficiency of a cell': (ne, '%'),
              'V': (V, 'Volts'), 'Ir': (Ir, 'Amps'),
              'Fleet Availability: %s' % fleetsize[0]: (fleetsize, 'Fleets')}
    static_plots(**kwargs)


if __name__ == '__main__':
    # Run SCENARIO 1
    # Pre-load the power request data using config.ini file
    #fleet = ElectrolyzerFleet("", "config.ini", "Electrolyzer")
    #fleet_test1(fleet)

    # Run SCENARIO 2
    # Use instantaneous power request with fleets specified in config.ini
    fleet = ElectrolyzerFleet("", "config.ini", "Electrolyzer", True)
    fleet_test2(fleet)
