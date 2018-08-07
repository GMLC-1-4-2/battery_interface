# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import sys
from dateutil import parser
from datetime import timedelta
from os.path import dirname, abspath

#import matplotlib.pyplot as plt

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

import numpy as np
#import matplotlib.pyplot as plt

from fleet_request import FleetRequest
from fleet_config import FleetConfig

# from fleets.home_ac_fleet.home_ac_fleet import HomeAcFleet
#from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet

from battery_inverter_fleet import BatteryInverterFleet
from helpers.historical_signal_helper import HistoricalSignalHelper
from helpers.clearing_price_helper import ClearingPriceHelper

from grid_info import GridInfo

class TradRegService():
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """

    def __init__(self, *args, **kwargs):
        self.sim_time_step = timedelta(hours=1)

        self._historial_signal_helper = HistoricalSignalHelper()
        self._clearing_price_helper = ClearingPriceHelper()

        self.grid = GridInfo('Grid_Info_DATA_2.csv')

    def request_loop(self, historial_signal_filename = '08 2017.xlsx', service_type = "Traditional", start_time = parser.parse("2017-08-01 16:00:00"), end_time = parser.parse("2017-08-01 21:00:00"),
                     clearing_price_filename = 'historical-ancillary-service-data-2017.xls', clearing_price_sheet_name = 'August_2017'): ### (TODO) add keywords for date and start hour, duration. add serv_type 'trad_reg'(default), 'dynm_reg'

        # start_time = parser.parse("2017-08-01 16:00:00")
        # end_time = parser.parse("2017-08-01 21:00:00")
        # Read Regulation control signal (RegA) from file: 2-sec interval.
        # df_RegA = pd.read_csv(filename, usecols=[0,1], header=0)

        # March through time (btw. start_time & end_time), store requested MW and responded MW every 2-sec in lists.
        # requests = []
        # responses = []
        # for row in df_RegA.iterrows():
        #     ts = row[1][0] # extract time stamp w/i a tuple.
        #     ts = parser.parse("2017-08-01 " + ts) # combine time stamp with date. ### hard-coded right now, extract date from column name later.
        #     if start_time <= ts < end_time:
        #         sim_step = timedelta(seconds=2) ### doesn't seem to be useful, but don't delete w/o confirmation.
        # TODO: Code below which determines "Assigned Regulation (MW)" (AReg) needs to be generalized for all device fleets rather than just for battery.
        # p = row[1][1] * (self.fleet.max_power_discharge * self.fleet.num_of_devices) * 0.4  ###
        #
        #         request, response = self.request(ts, sim_step, p)
        #         requests.append(request)
        #         responses.append(response)

        self._historial_signal_helper.read_and_store_historical_signals(historial_signal_filename, service_type)

        signals = self._historial_signal_helper.signals_in_range(start_time, end_time)

        sim_step = timedelta(seconds=2)
        requests = []
        responses = []

        for timestamp, power in signals.items():
            request, response = self.request(timestamp, sim_step, power)
            requests.append(request)
            responses.append(response)

        #print(requests)
        #print(responses)

        # Store the responses in a text file.
        with open('results.txt', 'w') as the_file:
        ### should add a step to clean the file first.
            for r in responses:
                ts = r.ts
                p_togrid = r.P_togrid
                p_service = r.P_service
                print(p_service)
                the_file.write("{p_togrid},{p_service}\n".format(p_togrid=p_togrid, p_service=p_service))

        self._clearing_price_helper.read_and_store_clearing_prices(clearing_price_filename, clearing_price_sheet_name)

        # Calculate hourly performance score and store in a dictionary.
        hourly_results = {}
        cur_time = start_time # need another loop if later want to calculate hourly score for multiple hours.
        one_hour = timedelta(hours=1)
        while cur_time < end_time - timedelta(minutes=65):

            # Generate 1-hour worth (65 min) request and response arrays for calculating scores.
            cur_end_time = cur_time + timedelta(minutes=65)
            request_array_2s = [r.P_req for r in requests if cur_time <= r.ts_req <= cur_end_time]
            response_array_2s = [r.P_service for r in responses if cur_time <= r.ts <= cur_end_time]
            request_array_2s = np.asarray(request_array_2s)
            response_array_2s = np.asarray(response_array_2s)
            # Slice arrays at 10s intervals - resulted arrays have 390 data points.
            request_array_10s = request_array_2s[::5]
            response_array_10s = response_array_2s[::5]

            # Calculate performance scores for current hour and store in a dictionary keyed by starting time.
            hourly_results[cur_time] = {}
            hourly_results[cur_time]['perf_score'] = self.perf_score(request_array_10s, response_array_10s)
            hourly_results[cur_time]['hr_int_MW'] = self.Hr_int_reg_MW(request_array_2s)
            #hourly_results[cur_time]['RMCP'] = self.get_RMCP()
            hourly_results[cur_time]['RMCP'] = self._clearing_price_helper.clearing_prices[cur_time]
            hourly_results[cur_time]['reg_clr_pr_credit'] = self.Reg_clr_pr_credit(hourly_results[cur_time]['RMCP'], hourly_results[cur_time]['perf_score'][0], hourly_results[cur_time]['hr_int_MW'])

            # Move to the next hour.
            cur_time += one_hour

        # Plot request and response signals and state of charge (SoC).
        P_request = [r.P_req for r in requests]
        P_responce = [r.P_service for r in responses]
        SOC = [r.soc for r in responses]
        n = len(P_request)
        t = np.asarray(range(n))*(2/3600)
        # plt.figure(1)
        # plt.subplot(211)
        # plt.plot(t, P_request, label='P Request')
        # plt.plot(t, P_responce, label='P Responce')
        # plt.ylabel('Power (kW)')
        # plt.legend(loc='upper right')
        # plt.subplot(212)
        # plt.plot(t, SOC, label='SoC')
        # plt.ylabel('SoC (%)')
        # plt.xlabel('Time (hours)')
        # plt.legend(loc='lower right')
        # plt.show()

        return hourly_results


    def request(self, ts, sim_step, p, q=0.0): # added input variables; what's the purpose of sim_step??
        fleet_request = FleetRequest(ts=ts, sim_step=sim_step, p=p, q=0.0)
        fleet_response = self._fleet.process_request(fleet_request,self.grid)
        #print(fleet_response.P_service)
        return fleet_request, fleet_response


    # Score the performance of device fleets (based on PJM Manual 12).
    # Take 65 min worth of 10s data (should contain 1,950 data values).
    def perf_score (self, request_array, response_array):
        max_corr_array = []
        max_index_array = []
        prec_score_array = []

        # In each 5-min of the hour, use max correlation to define "delay", "correlation" & "delay" scores.
        # There are twelve (12) 5-min in each hour.
        for i in range(12):

            # Takes 5-min of the input signal data.
            x = request_array[30 * i:30 * (i + 1)]
            #         print('x:', x)
            y = response_array[30 * i:30 * (i + 1)]

            # Refresh the array in each 5-min run.
            corr_score = []

            # If the regulation signal is nearly constant, then correlation score is calculated as:
            # 1 - absoluate of difference btw slope of request and response signals (determined by linear regression).
            std_dev_x = np.std(x)
            std_dev_y = np.std(y)
            if std_dev_x < 0.01: # need to vet the threshold later, not specified in PJM manual.
                axis = np.array(np.arange(30.))
                coeff_x = np.polyfit(axis, x, 1) # linear regression when degree = 1.
                coeff_y = np.polyfit(axis, y, 1)
                slope_x = coeff_x[0]
                slope_y = coeff_y[0]
                corr_score_val = max(0, 1 - abs(slope_x - slope_y)) # from PJM manual 12.
                max_index_array = np.append(max_index_array, 0)
                max_corr_array = np.append(max_corr_array, corr_score_val) # r cannot be calc'd for constant values in one or both arrays.
            # when request signal varies but response signal is constant, correlation and delay scores will be zero.
            elif std_dev_y < 0.00001:
                corr_score_val = 0
                max_index_array = np.append(max_index_array, 30)
                max_corr_array = np.append(max_corr_array, corr_score_val)
            else:
                # Calculate correlation btw the 5-min input signal and thirty 5-min response signals,
                # each is delayed at an additional 10s than the previous one; store results.
                # There are thirty (30) 10s in each 5min.
                for j in range(31):
                    y_ = response_array[30 * i + j:30 * (i + 1) + j]

                    #             # for debug use
                    #             print('y:', y)
                    #             x_axis_x = np.arange(x.size)
                    #             plt.plot(x_axis_x, x, "b")
                    #             plt.plot(x_axis_x, y, "r")
                    #             plt.show()

                    # Calculate Pearson Correlation Coefficient btw input and response for the 10s step.
                    corr_r = np.corrcoef(x, y_)[0, 1]
                    # Correlation scores stored in an numpy array.
                    corr_score = np.append(corr_score, corr_r)
                    #         print('corr_score:', corr_score)

                # locate the 10s moment(step) at which correlation score was maximum among the thirty calculated; store it.
                max_index = np.where(corr_score == max(corr_score))[0][0]
                max_index_array = np.append(max_index_array, max_index)  # array
                # Find the maximum score in the 5-min; store it.
                max_corr_array = np.append(max_corr_array, corr_score[max_index])  # this is the correlation score array

            # Calculate the coincident delay score associated with max correlation in each 5min period.
            delay_score = np.absolute((10 * max_index_array - 5 * 60) / (5 * 60))  # array

            # Calculate error at 10s intervals and store in an array.
            error = np.absolute(y - x) / (np.absolute(x).mean())
            # Calculate 5-min average Precision Score as the average error.
            prec_score = max(0, 1 - 1 / 30 * error.sum())
            prec_score_array = np.append(prec_score_array, prec_score)

        # for debug use
        print('delay_score:', delay_score)
        print('max_index_array:', max_index_array)
        print('max_corr_array:', max_corr_array)
        print('prec_score_array:', prec_score_array)

        # calculate average "delay", "correlation" and "precision" scores for the hour.
        Delay_score = delay_score.mean()
        Corr_score = max_corr_array.mean()
        Prec_score = prec_score_array.mean()

        #     # for debug use
        #     x_axis_error = np.arange(error.size)
        #     plt.scatter(x_axis_error, error)
        #     plt.show()

        # Calculate the hourly overall Performance Score.
        Perf_score = (Delay_score + Corr_score + Prec_score)/3

        # # Plotting and Printing results
        # x_axis_sig = np.arange(request_array[0:360].size)
        # x_axis_score = np.arange(max_corr_array.size)
        #
        # plt.figure(1)
        # plt.subplot(211)
        # plt.plot(x_axis_sig, request_array[0:360], "b")
        # plt.plot(x_axis_sig, response_array[0:360], "r")
        # plt.legend(('RegA signal', 'CReg response'), loc='lower right')
        # plt.show()
        #
        # plt.figure(2)
        # plt.subplot(212)
        # plt.plot(x_axis_score, max_corr_array, "g")
        # plt.plot(x_axis_score, delay_score, "m")
        # plt.legend(('Correlation score', 'Delay score'), loc='lower right')
        # plt.show()
        #
        # print('Delay_score:', Delay_score)
        # print('Corr_score:', Corr_score)
        # print('Prec_score:', Prec_score)
        # print('Perf_score:', Perf_score)

        return (Perf_score, Delay_score, Corr_score, Prec_score)


    # calculate "Hourly-integrated Regulation MW".
    # based on PJM Manual 28 (need to verify definition, not found in manual).
    def Hr_int_reg_MW (self, input_sig):
        # Take one hour of 2s RegA data
        Hourly_Int_Reg_MW = np.absolute(input_sig).sum() * 2 / 3600
        # print(Hourly_Int_Reg_MW)
        return Hourly_Int_Reg_MW


    # looks up the regulation market clearing price (RMCP).
    # the RMCP and its components are stored in a 1-dimensional array.
    # Use Aug 1st, 2017, 4-5PM data.
    # def get_RMCP(self): ### needs to be expanded to include date and time in keywords.
    #     raw_pr_dataframe = pd.read_excel('historical-ancillary-service-data-2017.xls',
    #                                      sheetname='August_2017', header=0)
    #     #     print(raw_pr_dataframe)
    #
    #     raw_pr_array = raw_pr_dataframe.values  # convert from pandas dataframe to numpy array.
    #     RMCP = raw_pr_array[80][4]  # Regulation Market Clearing Price.
    #     RMCCP = raw_pr_array[80][6]  # Regulation Market Capability Clearing Price.
    #     RMPCP = raw_pr_array[80][7]  # Regulation Market Performance Clearing Price.
    #
    #     return (RMCP, RMPCP, RMCCP)


    # calculates hourly "Regulation Market Clearing Price Credit" for a device fleet for the regulation service provided.
    # based on PJM Manual 28.
    def Reg_clr_pr_credit(self, RM_pr, pf_score, reg_MW):
        # Arguments:
        # RM_pr - RMCP price components for the hour.
        # pf_score - performance score for the hour.
        # reg_MW - "Hourly-integrated Regulation MW" for the hour.

        # prepare key parameters for calculation.
        RMCCP = RM_pr[1]
        RMPCP = RM_pr[2]

        # "mileage ratio" equals "1" for traditional regulation (i.e. RegA); is >1 for dynamic regulation.
        mi_ratio = 1

        print("Hr_int_reg_MW:", reg_MW)
        print("Pf_score:", pf_score)
        print("RMCCP:", RMCCP)
        print("RMPCP:", RMPCP)

        # calculate "Regulation Market Clearing Price Credit" and two components.
        # minimum perf score is 0.25, otherwise forfeit regulation credit (and lost opportunity) for the hour (m11 3.2.10).
        if pf_score < 0.25:
            Reg_RMCCP_Credit = 0
            Reg_RMPCP_Credit = 0
        else:
            Reg_RMCCP_Credit = reg_MW * pf_score * RMCCP
            Reg_RMPCP_Credit = reg_MW * pf_score * mi_ratio * RMPCP
        Reg_Clr_Pr_Credit = Reg_RMCCP_Credit + Reg_RMPCP_Credit

        # print("Reg_Clr_Pr_Credit:", Reg_Clr_Pr_Credit)
        # print("Reg_RMCCP_Credit:", Reg_RMCCP_Credit)
        # print("Reg_RMPCP_Credit:", Reg_RMPCP_Credit)

        # "Lost opportunity cost credit" (for energy sources providing regulation) is not considered,
        # because it does not represent economic value of the provided service.

        return (Reg_Clr_Pr_Credit, Reg_RMCCP_Credit, Reg_RMPCP_Credit)



    def change_config(self):
        fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=0.1)
        self._fleet.change_config(fleet_config)

    # def normalize_p(self, p):
    #     return p

    @property
    def fleet(self):
        return self._fleet

    @fleet.setter
    def fleet(self, value):
        self._fleet = value


# run from this file
if __name__ == '__main__':
    service = TradRegService()

    #battery_inverter_fleet = BatteryInverterFleet('C:\\Users\\jingjingliu\\gmlc-1-4-2\\battery_interface\\src\\fleets\\battery_inverter_fleet\\config_CRM.ini')
    battery_inverter_fleet =  BatteryInverterFleet() #temporary for the purpose of getting dummy response
    service.fleet = battery_inverter_fleet

    # Test request_loop()
    fleet_response = service.request_loop()
    print(fleet_response)


#cd C:\Users\jingjingliu\gmlc-1-4-2\battery_interface\src\services\trad_reg_service\
#python trad_reg_service.py
