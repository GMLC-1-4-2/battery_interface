# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleets.fuel_cell_fleet.fuelcell_fleet import FuelCellFleet, static_plots
from fleet_request import FleetRequest
from datetime import datetime, timedelta
from scipy.io import loadmat
base_path = dirname(abspath(__file__))


def fleet_test1(fleet):

    """
    SCENARIO 1: Pre-load the power request curve
    """

    # Get simulation duration based on pre-loaded power curve data
    n = fleet.timespan

    # Create fleet request
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts+i*dt), sim_step=dt, p=None, q=None) for i in range(n)]

    # Process the request
    p_resp, q_resp, soc, ne, Vr, Ir, status, fleetsize = [], [], [], [], [], [], [], []
    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        p_resp.append(fleet_response.P_togrid)
        q_resp.append(fleet_response.Q_togrid)
        soc.append(fleet_response.soc)
        ne.append(fleet_response.ne)
        Vr.append(fleet_response.v_real)
        Ir.append(fleet_response.Ir)
        status.append(fleet_response.status)
        fleetsize.append(fleet_response.fc_fleet)

    # Simulation results
    stat = "fully charged at %s sec." % str(sum(status))

    # Plot the results
    kwargs = {'P_response': (p_resp, 'kW'),
              'Q_request': (q_resp, 'kVAr'), 'SoC ('+stat+')': (soc, 'Pa'),
              'Energy efficiency of a cell': (ne, '%'),
              'V_real': (Vr, 'Volts'), 'Ir': (Ir, 'Amps.'),
              'Fleet Availability: %s' % fleetsize[0]: (fleetsize, 'Fleets')}
    static_plots(**kwargs)


def fleet_test2(fleet):
    """
    SCENARIO 2: Use instantaneous power request
    Number of FuelCells (Nfc) needs to be specified in the
    config.ini file
    """
    p_data = loadmat(join(base_path, 'pdata.mat'), squeeze_me=True)
    time = p_data['TT']

    # Power direction wrt the Grid.
    # Ey is negative power
    p_req = p_data['PP']

    # Create fleet request
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts+i*dt), sim_step=dt, p=v, q=None) for i, v in enumerate(p_req)]

    # Process the request
    p_resp, q_resp, soc, ne, Vr, Ir, status, fleetsize = [], [], [], [], [], [], [], []
    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        p_resp.append(fleet_response.P_togrid)
        q_resp.append(fleet_response.Q_togrid)
        soc.append(fleet_response.soc)
        ne.append(fleet_response.ne)
        Vr.append(fleet_response.v_real)
        Ir.append(fleet_response.Ir)
        status.append(fleet_response.status)
        fleetsize.append(fleet_response.fc_fleet)

    # Simulation results
    stat = "fully charged at %s sec." % str(sum(status))

    # Plot the results
    kwargs = {'P_request': (p_req, 'kW'), 'P_response': (p_resp, 'kW'),
              'Q_request': (q_resp, 'kVAr'), 'SoC ('+stat+')': (soc, 'Pa'),
              'Energy efficiency of a cell': (ne, '%'),
              'V_real': (Vr, 'Volts'), 'Ir': (Ir, 'Amps.'),
              'Fleet Availability: %s' % fleetsize[0]: (fleetsize, 'Fleets')}
    static_plots(**kwargs)


if __name__ == '__main__':
    # Run SCENARIO 1
    # Pre-load the power request data using config.ini file
    fleet = FuelCellFleet("", "config.ini", "FuelCell")
    fleet_test1(fleet)

    # Run SCENARIO 2
    # Use instantaneous power request with fleets specified in config.ini
    #fleet = FuelCellFleet("", "config.ini", "FuelCell", True)
    #fleet_test2(fleet)
