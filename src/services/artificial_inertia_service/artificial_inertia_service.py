# -*- coding: utf-8 -*- {{{
#
# Your license here
# Created by Yuan Liu
# }}}

import sys
from dateutil import parser
from datetime import datetime, timedelta
from os.path import dirname, abspath, join
from grid_info_artificial_inertia import GridInfo
import matplotlib.pyplot as plt
import csv
import numpy as np

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleet_request import FleetRequest
from fleet_config import FleetConfig


class ArtificialInertiaService():
    def __init__(self, fleet_device=None):
        self.fleet_device = fleet_device

    @property
    def fleet(self):
        return self.fleet_device

    @fleet.setter
    def fleet(self, value):
        self.fleet_device = value

    def request_loop(self, start_time, sim_step):
        responses = []

        #inittime = parser.parse("2018-10-12 00:00:00")
        #delt = timedelta(seconds=2 / 60)
        delt = sim_step
        cur_time = start_time
        end_time = cur_time + timedelta(seconds=149)
        while cur_time < end_time:
            fleet_request = FleetRequest(cur_time, delt, start_time)
            fleet_response = self.fleet_device.process_request(fleet_request)
           # fleet_response = self.fleet_device.frequency_watt(fleet_request)

            responses.append(fleet_response)
            cur_time += delt
            print("{}".format(cur_time))

        return responses

    def calculation(self, fleetname, responses, start_time, **kwargs):
        # Do calculation with responses
        # responses []
        p_service = []
        p_togrid = []
        t = []
        f = []

        sum = 0
        grid = GridInfo('Grid_Info_data_artificial_inertia.csv')

        # extract time, frequency and power responses data
        for response in responses:

            f.append(grid.get_frequency(response.ts, 0, start_time))
            p_service.append(response.P_service)
            p_togrid.append(response.P_togrid)
            t.append(response.ts)

        integration_test_result_dir = join( dirname(dirname(dirname(abspath(__file__))) ), 'integration_test', 'artificial_inertia')

        # plot extracted data
        # time versus Pservice
        fig, ax1 = plt.subplots()
        ax1.set_title('Pservice and Ptogrid Responses')
        l1, = ax1.plot(t, p_service, 'b-', label='service power')
        l2, = ax1.plot(t, p_togrid, 'k-', label='power to grid')
        ax1.set_ylabel('Power (kW)', color='b')
        ax1.tick_params('y', colors='b')
        ax1.set_xlabel('Time')

        ax2 = ax1.twinx()
        l3, = ax2.plot(t,  f, 'r-', label='frequency')
        ax2.set_ylabel('f (Hz)', color='r')
        ax2.tick_params('y', colors='r')

        plt.legend(handles=[l1, l2, l3])

        plot_filename = datetime.now().strftime('%Y%m%d') + '_ArtificialInertia_' + fleetname + '.png'
        plot_dir = integration_test_result_dir

        plt.savefig(join(plot_dir, plot_filename), bbox_inches='tight')

        # frequency versus Pservice
        fig2, ax2 = plt.subplots()
        ax2.set_title('Frequency versus Pservice')
        ax2.plot(f, p_service, 'b-', label='service power')
        ax2.set_ylabel('Power (kW)', color='b')
        ax2.tick_params('y', colors='b')
        ax2.set_xlabel('frequency (Hz)')

        plot_filename = datetime.now().strftime('%Y%m%d') + '_ArtificialInertia_' + fleetname + '_f_Pservice.png'
        plot_dir = integration_test_result_dir

        plt.savefig(join(plot_dir, plot_filename), bbox_inches='tight')

        # calculate performance metrics
        p_base = (np.array(p_service) - np.array(p_togrid)).tolist()
        service_energy = 0.0
        base_energy = 0.0

        if kwargs != {}:
            if len(kwargs) != 2:
                raise ValueError('Don''t forget to include both start and end time for metrics calculation.')
            metrics_calc_start_time = kwargs['metrics_calc_start_time']  # the beginning of timeframe to calculate metrics
            metrics_calc_end_time = kwargs['metrics_calc_end_time']  # the end of timeframe to calculate metrics

            if metrics_calc_start_time < start_time:
                raise ValueError('Start time for metrics calculation cannot be smaller than service start time.')
            elif metrics_calc_end_time > start_time + timedelta(seconds=149):
                raise ValueError('End time for metrics calculation cannot exceed total period of artificial inertia grid service.')

            for tstart_idx in range(1, len(t)+1):
                if t[tstart_idx-1] < metrics_calc_start_time and metrics_calc_start_time <= t[tstart_idx]:
                    break

            for tend_idx in range(1, len(t)+1):
                if t[tend_idx-1] < metrics_calc_end_time and metrics_calc_end_time <= t[tend_idx]:
                    break

            for t_idx in range(tstart_idx+1, tend_idx):
                service_energy += ( t[t_idx] - t[t_idx-1] ).total_seconds() * ( p_service[t_idx-1] + p_service[t_idx] ) * 0.5
                base_energy += ( t[t_idx] - t[t_idx-1] ).total_seconds() * ( p_base[t_idx-1] + p_base[t_idx] ) * 0.5

            try:
                service_efficacy = service_energy / base_energy
            except ZeroDivisionError:
                print('Base energy is zero.')

            # print(service_efficacy)

        else:
            for t_idx in range(1, len(t)):
                service_energy += ( t[t_idx] - t[t_idx - 1] ).total_seconds() * ( p_service[t_idx - 1] + p_service[t_idx]) * 0.5
                base_energy += ( t[t_idx] - t[t_idx - 1] ).total_seconds() * ( p_base[t_idx - 1] + p_base[t_idx] ) * 0.5

            try:
                service_efficacy = service_energy / base_energy
            except ZeroDivisionError:
                print('Base energy is zero.')

        # write results into .csv file
        csv_file_name = datetime.now().strftime('%Y%m%d') + '_ArtificialInertia_' + fleetname + '.csv'

        with open(join(integration_test_result_dir, csv_file_name), 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            # csvwriter = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(['time', 'frequency', 'service power', 'power to grid'])
            for tidx in range(len(t)):
                csvwriter.writerow([t[tidx].strftime('%m/%d/%Y, %H:%M:%S'), str(f[tidx]), str(p_service[tidx]), str(p_togrid[tidx])])
            csvwriter.writerow(['service efficacy=%06.4f' % service_efficacy])
            # or csvwriter.writerow(['service efficacy={:06.4f}'.format(service_efficacy)])

        csvfile.close()

        return service_efficacy, p_service, p_togrid, t, f


if __name__ == "__main__":
    #import numpy as np
    #import matplotlib.pyplot as plt
    from grid_info_artificial_inertia import GridInfo
    #from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet
    from fleets.home_ac_fleet.home_ac_fleet import HomeAcFleet

    # Create a fleet and pass in gridinfo (contains the frequency from CSV file)
    grid = GridInfo('Grid_Info_data_artificial_inertia.csv')
    fleet_device = BatteryInverterFleet(GridInfo=grid)  # establish the battery inverter fleet with a grid
    #fleet_device = HomeAcFleet(GridInfo=grid)

    # Create a service
    service = ArtificialInertiaService(fleet_device)
    responses = service.request_loop()
    avg = service.calculation(responses)

    # Plot, print to screen ...
    # print(avg)
    # pickfreq = grid.get_frequency(parser.parse('2018-10-12 00:02:00'), 0)
    # print(pickfreq)
