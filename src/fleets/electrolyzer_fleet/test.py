# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleets.electrolyzer_fleet.ey_fleet import ElectrolyzerFleet, static_plots
from scipy.io import loadmat
base_path = dirname(abspath(__file__))


def fleet_test1(fleet):

    """
    SCENARIO 1: Pre-load the power request curve
    Number of electrolyzers (Ne) automatically computed based on the
    area of te power request curve
    """
    # Set p_req as None in the model
    # Get simulation duration based on pre-loaded power curve data
    n = fleet.timespan

    # Process the request
    soc, Ptot, m_dotH2, moles, V, Ir = [], [], [], [], [], []
    for i in range(n):
        fleet_response = fleet.process_request(i)
        soc.append(fleet_response.soc_per)
        Ptot.append(fleet_response.P_tot)
        m_dotH2.append(fleet_response.m_dotH2)
        moles.append(fleet_response.moles)
        V.append(fleet_response.V)
        Ir.append(fleet_response.Ir)
        if not fleet_response.isAvail:
            break

    # Print the results
    kwargs = {'Ptot': (Ptot, 'Watts'), 'm_dotH2': (m_dotH2, 'Kg/s'),
              'SoC': (soc, '%'), 'moles': (moles, 'mol'),
              'V': (V, 'Volts'), 'Ir': (Ir, 'Amps')}
    static_plots(**kwargs)


def fleet_test2(fleet):
    """
    SCENARIO 2: Use instantaneous power request
    Number of electrolyzers (Ne) needs to be specified in the
    config.ini file
    """
    p_data = loadmat(join(base_path, 'pdata.mat'), squeeze_me=True)
    time = p_data['TT']

    # Power direction wrt the Grid.
    # Ey is negative power
    p_req = p_data['PP']

    # base load of 20% of initial power requirement
    bload = p_req[0]*0.2

    p_curve = [abs(p_req[i])-bload if p_req[i] < 0 else bload for i in range(len(p_req))]

    # Process the request
    soc, Ptot, m_dotH2, moles, V, Ir, P = [], [], [], [], [], [], []
    for i in range(len(p_curve)):
        fleet_response = fleet.process_request(p_req[i])
        soc.append(fleet_response.soc_per)
        Ptot.append(fleet_response.P_tot)
        m_dotH2.append(fleet_response.m_dotH2)
        moles.append(fleet_response.moles)
        V.append(fleet_response.V)
        Ir.append(fleet_response.Ir)
        P.append(fleet_response.Pl)
        if not fleet_response.isAvail:
            break

    # Print the results
    kwargs = {'Ptot': (Ptot, 'Watts'), 'm_dotH2': (m_dotH2, 'Kg/s'),
              'SoC': (soc, '%'), 'moles': (moles, 'mol'),
              'V': (V, 'Volts'), 'Ir': (Ir, 'Amps')}
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
