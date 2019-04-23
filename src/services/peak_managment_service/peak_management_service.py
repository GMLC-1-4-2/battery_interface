# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
import matplotlib.pyplot as plt


from dateutil import parser
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import configparser

import utils
from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse
from fleet_config import FleetConfig

from utils import ensure_ddir

class PeakManagementService:
    """
    The peak management service short summary
    """

    def __init__(self, fleet=None, sim_step = timedelta(minutes=1), *args, **kwargs):
        # The scope of the project is to test service with one fleet...
        self.fleet = fleet

        # Get cur directory
        self.base_path = dirname(abspath(__file__))

        # Read config file
        config_header = 'config'
        self.config = configparser.ConfigParser()
        self.config.read(join(self.base_path, 'config.ini'))

        self.name = self.config.get(config_header, 'name', fallback='Peak Management Service')
        self.capacity_scaling_factor = float(self.config.get(config_header, 'capacity_scaling_factor', fallback=1.0))
        self.f_reduction = float(self.config.get(config_header, 'f_reduction', fallback=0.1))
        self.drive_cycle_file = self.config.get(config_header, 'drive_cycle_file',
                                                fallback='drive.cycle.summer.peaky.csv')
        self.drive_cycle_file = join(self.base_path, 'data', self.drive_cycle_file)

        # Establish a default simulation timestep (will always be 1-hour as far as I know)...
        self.sim_step = sim_step

        # Long term, we don't want a drive cycle, we want to call some kind of daily
        # load forecast service that a higher-level function in the software provides.
        # But for now, our whole purpose is testing...
        #
        # This data frame has columns (year, month_abbr, day, hour, load_forecast_mw), where month is
        # the three-letter month abbreviation (Jan, Feb, etc.) and all others are numeric...
        self.drive_cycle = pd.read_csv(self.drive_cycle_file)

        # There may be more straightforward ways to do this...just want to add a datetime object
        # matching the drive cycle's year, month_abbr, day, hour info...
        self.drive_cycle["month"] = [utils.month_abbr_to_num(abbr) for abbr in self.drive_cycle["month"]]

        # self.drive_cycle["dt"] = [datetime(self.drive_cycle["year"],
        #                                    self.drive_cycle["month_num"],
        #                                    self.drive_cycle["day"],
        #                                    self.drive_cycle["hour"], 0, 0)]

        self.drive_cycle["dt"] = pd.to_datetime(self.drive_cycle[["year", "month", "day", "hour"]])

        # Ideally the fleet could tell us its capacity and we compute the scaling_factor from that
        # and the maximum value in the drive cycle...
        #self.drive_cycle.load_forecast_mw /= self.capacity_scaling_factor
        '''
        # normalizes drive cycle and scales to fleet service capacity
        self.drive_cycle.load_forecast_mw *= self.fleet.assigned_service_kW()/max(self.drive_cycle.load_forecast_mw)
        
        # Find the "annual" peak (largest peak in our drive cycle really) and the desired new peak...
        #self.annual_peak = max(self.drive_cycle.load_forecast_mw)
        self.annual_peak = max(self.drive_cycle.load_forecast_mw)
        self.mw_target = self.annual_peak * (1 - self.f_reduction)
        '''
        # TODO:  Initialize something to hold stats

    def request_loop(self, start_time,fleet_name="PVInverterFleet"):
        cycle = 24
        ndx_start = 0
        ndx_end = ndx_start + cycle
        #device_ts = 
                # normalizes drive cycle and scales to fleet service capacity
        self.drive_cycle.load_forecast_mw *= self.fleet.assigned_service_kW()/max(self.drive_cycle.load_forecast_mw)
        
        # Find the "annual" peak (largest peak in our drive cycle really) and the desired new peak...
        #self.annual_peak = max(self.drive_cycle.load_forecast_mw)
        self.annual_peak = max(self.drive_cycle.load_forecast_mw)
        self.mw_target = self.annual_peak * (1 - self.f_reduction)
        requests = []
        responses = []
#        while ndx_end < len(self.drive_cycle.dt):   # Loop over days...
        while ndx_end <= len(self.drive_cycle.dt):   # Loop over days...
            dt_day = self.drive_cycle.dt[ndx_start:ndx_end]
            dt_day.reset_index(drop=True, inplace=True)
            mw_day = self.drive_cycle.load_forecast_mw[ndx_start:ndx_end]
            mw_day.reset_index(drop=True, inplace=True)
            p_needed = [max(0, mw_day[i] - self.mw_target) for i in range(cycle)]
            
            for index, item in enumerate(p_needed):
                if item == 0:
                    p_needed[index] = None
            
            ndx_start += 24
            ndx_end += 24

            # No need to work on days without high peaks
            #if max(mw_day) <= self.mw_target:
            for i in range(24):
                for j in range(int(3600/self.sim_step.seconds)):
                    fleet_request = FleetRequest(ts=dt_day[i]+j*self.sim_step, sim_step=self.sim_step, start_time=start_time, p=p_needed[i])
                    fleet_response = self.fleet.process_request(fleet_request)
            # store requests and responses
                    requests.append(fleet_request)
                    responses.append(fleet_response)
                    print(responses[-1].P_service)
            '''
            else:
                # Get a 24-hour forecast from fleet
                forecast_requests = [FleetRequest(ts=dt_day[i], sim_step=self.sim_step, p=p_needed[i]) for i in range(cycle)]
                forecast_response = self.fleet.forecast(forecast_requests)
                
                # See if the forecast can meet the desired load
                deficit = [forecast_response[i].P_service - p_needed[i] for i in range(24)]
                insufficient = [deficit[i] < 0 for i in range(cycle)]
                if any(insufficient):
                    # TODO:  NEED TO LOOP BACK AND REBUILD requests until we have a 24-hour request we know can be met
                    pass
                
                # Now we know what the fleet can do, so ask it to do it
                for i in range(24):
                    fleet_request = FleetRequest(ts=dt_day[i], sim_step=self.sim_step, start_time=start_time, p=forecast_response[i].P_service)
                    fleet_response = self.fleet.process_request(fleet_request)
                    # TODO:  store performance stats

                    requests.append(fleet_request)
                    responses.append(fleet_response)
                    print(responses[-1].P_service)
            '''        
        request_list_1h = []
        for r in requests:
            if r.P_req is not None:
                request_list_1h.append((r.ts_req, r.P_req / 1000))
            else:
                request_list_1h.append((r.ts_req, r.P_req))
        request_df_1h = pd.DataFrame(request_list_1h, columns=['Date_Time', 'Request'])
        
        if 'battery' in fleet_name.lower():
            # Include battery SoC in response list for plotting purposes
            response_list_1h = [(r.ts, r.P_service / 1000, r.P_togrid, r.P_base, r.soc) for r in responses]
            response_df_1h = pd.DataFrame(response_list_1h, columns=['Date_Time', 'Response', 'P_togrid', 'P_base', 'SoC'])
        else:
            
            response_list_1h = [(r.ts, np.nan if r.P_service is None else r.P_service / 1000, r.P_togrid, r.P_base) for r in responses]
            response_df_1h = pd.DataFrame(response_list_1h, columns=['Date_Time', 'Response', 'P_togrid','P_base'])

        # This merges/aligns the requests and responses dataframes based on their time stamp 
        # into a single dataframe
        df_1h = pd.merge(
            left=request_df_1h,
            right=response_df_1h,
            how='left',
            left_on='Date_Time',
            right_on='Date_Time')

        df_1h['P_togrid'] = df_1h['P_togrid'] / 1000
        df_1h['P_base'] = df_1h['P_base'] / 1000

        # Plot entire analysis period results and save plot to file
        # We want the plot to cover the entire df_1h dataframe
        plot_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'integration_test', 'peak_management_service')
        ensure_ddir(plot_dir)
        plot_filename = 'SimResults_PeakManagement_' + fleet_name + '_' + datetime.now().strftime('%Y%m%dT%H%M')  + '.png'
        plt.figure(1)
        plt.figure(figsize=(15, 8))
        plt.subplot(211)
        if not(all(pd.isnull(df_1h['Request']))):
            plt.plot(df_1h.Date_Time, df_1h.Request, label='P_Request')
        if not(all(pd.isnull(df_1h['Response']))):
            plt.plot(df_1h.Date_Time, df_1h.Response, label='P_Response')
        if not(all(pd.isnull(df_1h['P_togrid']))):
            plt.plot(df_1h.Date_Time, df_1h.P_togrid, label='P_togrid')
        if not(all(pd.isnull(df_1h['P_base']))):
            plt.plot(df_1h.Date_Time, df_1h.P_base, label='P_base')
        plt.ylabel('Power (MW)')
        plt.legend(loc='best')
        if 'battery' in fleet_name.lower():
            if not(all(pd.isnull(df_1h['SoC']))):
                plt.subplot(212)
                plt.plot(df_1h.Date_Time, df_1h.SoC, label='SoC')
                plt.ylabel('SoC (%)')
                plt.xlabel('Time')
        plt.savefig(join(plot_dir, plot_filename), bbox_inches='tight')
        plt.close()
        
        # compute and report metrics to csv
        perf_metrics = pd.DataFrame(columns=['Service_efficacy'])
        perf_metrics['Service_efficacy'] = pd.Series(min(1,abs(df_1h.Response).sum()/abs(df_1h.Request).sum()))
        metrics_filename = 'Performance_PeakManagement_' + fleet_name + '_' + datetime.now().strftime('%Y%m%dT%H%M')  + '.csv'
        perf_metrics.to_csv(join(plot_dir, metrics_filename) )
        
    def process_stats(self, dh_1h):
        pass
        # TODO:  Aggregate up the fleet's performance stats and...do what?  Print them?  Write them to a file?
