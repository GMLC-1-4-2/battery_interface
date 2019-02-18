# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleets.fuel_cell_fleet.fuelcell_fleet import FuelCellFleet, static_plots
from scipy.io import loadmat
base_path = dirname(abspath(__file__))


def fleet_test1(fleet):

    """
    SCENARIO 1: Pre-load the power request curve
    """

    # Get simulation duration based on pre-loaded power curve data
    n = fleet.timespan

    # Process the request
    soc, P_tank, ne, moles, Vi, Ir, P = [], [], [], [], [], [], []
    for i in range(n):
        fleet_response = fleet.process_request(i)
        soc.append(fleet_response.soc_per)
        P_tank.append(fleet_response.P_tank)
        ne.append(fleet_response.ne)
        moles.append(fleet_response.moles)
        Vi.append(fleet_response.Vi)
        Ir.append(fleet_response.Ir)
        P.append(fleet_response.Pl)
        if not fleet_response.isAvail:
            break

    # Print the results
    kwargs = {'P_tank': (P_tank, 'Watts'), 'ne': (ne, '%'),
              'SoC': (soc, '%'), 'moles': (moles, 'mol'),
              'Vi': (Vi, 'Volts'), 'Ir': (Ir, 'Amps')}
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

    # base load of 20% of initial power requirement
    #bload = p_req[0]*0.2

    #p_curve = [abs(p_req[i])-bload if p_req[i] < 0 else bload for i in range(len(p_req))]

    # Process the request
    soc, P_tank, Qh2_m, moles, Vr, Ir = [], [], [], [], [], []
    for i in range(len(p_req)):
        fleet_response = fleet.process_request(p_req[i])
        soc.append(fleet_response.soc_per)
        P_tank.append(fleet_response.P_tank)
        Qh2_m.append(fleet_response.Qh2_m)
        moles.append(fleet_response.moles)
        Vr.append(fleet_response.Vr)
        Ir.append(fleet_response.Ir)
        if not fleet_response.isAvail:
            break

    # Print the results
    kwargs = {'P_tank': (P_tank, 'Watts'), 'Qh2_m': (Qh2_m, 'mol/s'),
              'SoC': (soc, '%'), 'moles': (moles, 'mol'),
              'Vr': (Vr, 'Volts'), 'Ir': (Ir, 'Amps')}
    static_plots(**kwargs)


if __name__ == '__main__':
    # Run SCENARIO 1
    # Pre-load the power request data using config.ini file
    #fleet = FuelCellFleet("", "config.ini", "FuelCell")
    #fleet_test1(fleet)

    # Run SCENARIO 2
    # Use instantaneous power request with fleets specified in config.ini
    fleet = FuelCellFleet("", "config.ini", "FuelCell", True)
    fleet_test2(fleet)
