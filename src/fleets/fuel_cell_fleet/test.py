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
from grid_info_artificial_inertia import GridInfo
from datetime import datetime, timedelta
from scipy.io import loadmat
from matplotlib.pyplot import show, grid, subplots
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
base_path = dirname(abspath(__file__))


def fleet_test(fleet):

    p_data = loadmat(join(base_path, 'pdata.mat'), squeeze_me=True)
    time = p_data['TT']

    # Power direction wrt the Grid.
    # FC is positive power to grid
    p_req = p_data['PP']

    # Power curve to have bot negative and positive
    bload = p_req[0] * 0.2
    p_curve = [bload if v < 0 else -(abs(v)-bload-80) for _, v in enumerate(p_req)]

    # Create fleet request
    ts = datetime.utcnow()
    dt = timedelta(seconds=1)
    fleet_request = [FleetRequest(ts=(ts+i*dt), sim_step=dt, p=v, q=None) for i, v in enumerate(p_curve)]

    # Process the request
    P_togrid, Q_togrid, soc, ne, Eff_discharge, Vr, Ir, status, fleetsize, ts = [], [], [], [], [], [], [], [], [], []
    for fr in fleet_request:
        fleet_response = fleet.process_request(fr)
        P_togrid.append(fleet_response.P_togrid)
        print(P_togrid)
        Q_togrid.append(fleet_response.Q_togrid)
        soc.append(fleet_response.E)
        ne.append(fleet_response.ne)
        Eff_discharge.append(fleet_response.Eff_discharge)
        Vr.append(fleet_response.V)
        Ir.append(fleet_response.Ir)
        ts.append(fleet_response.ts)
        status.append(fleet_response.status)
        fleetsize.append(fleet_response.fc_fleet)

    # Forecast
    print("::FORECAST MODE::")
    forecast_fleet = fleet.forecast(fleet_request)
    p_response, energy_stored = [], []
    for i in range(len(forecast_fleet)):
        p_response.append(forecast_fleet[i].P_togrid)
        energy_stored.append(forecast_fleet[i].E)

    # Simulation results
    stat = "fully discharged at %s sec." % str(sum(status))

    # Generate the impact metrics file
    fleet.output_metrics('impact_metrics_%s' % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S')))

    # Plot the results
    kwargs = {'P_request': (p_curve, 'kW'), 'P_response': (P_togrid, 'kW'),
              'Q_request': (Q_togrid, 'kVAr'), 'SoC ('+stat+')': (soc, '%'),
              'Charging Efficiency': (Eff_discharge, '%'), 'Energy efficiency of a cell': (ne, '%'),
              'V_real': (Vr, 'Volts'), 'Ir': (Ir, 'Amps.'),
              'Fleet Availability: %s' % fleetsize[0]: (fleetsize, 'Fleets')}
    static_plots(**kwargs)

    fig1, y1 = subplots(figsize=(20, 12))
    p1, = y1.plot(ts, p_curve, label='P_request')
    y1.axhline(y=0, color='r', linestyle='-')
    p2, = y1.plot(ts, P_togrid, label='P_response')
    y1.set_ylabel('P(kW)')
    y2 = y1.twinx()
    p3, = y2.plot(ts, soc, label='SoC', color='g')
    y2.set_ylabel('SoC(%)')
    plots = [p1, p2, p3]
    y1.set_xlabel('DateTime (mm-dd H:M:S)')
    y1.legend(plots, [l.get_label() for l in plots])
    grid()
    show()
    fig1.savefig(join(base_path, "FC_result_P_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                 bbox_inches='tight')


if __name__ == '__main__':

    grid_dat = GridInfo('Grid_Info_data_artificial_inertia.csv')
    fleet = FuelCellFleet(grid_dat, "config.ini", "FuelCell", False)
    fleet_test(fleet)
