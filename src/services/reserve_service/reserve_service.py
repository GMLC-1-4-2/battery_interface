# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

# Import Python packages
import sys
from dateutil import parser
from datetime import datetime, timedelta
from os.path import dirname, abspath, join
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# Import modules from "src\services"
from fleet_request import FleetRequest
from fleet_config import FleetConfig
from utils import ensure_ddir

from pdb import set_trace as bp

from services.reserve_service.helpers.historical_signal_helper import HistoricalSignalHelper
from services.reserve_service.helpers.clearing_price_helper import ClearingPriceHelper


# Class for synchronized reserve service.
class ReserveService():
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """
    _fleet = None

    def __init__(self, *args, **kwargs):
        self._historial_signal_helper = HistoricalSignalHelper()
        self._clearing_price_helper = ClearingPriceHelper()

    # The "request_loop" function is the workhorse that manages high-level monthly loops and sending requests & retrieving responses.
    # The time step for simulating fleet's response is at 1 minute.
    # It returns a 2-level dictionary; 1st level key is the month.
    # TODO: [minor] currently, the start and end times are hardcoded. Ideally, they would be based on promoted user inputs.
    def request_loop(self,
                     start_time=parser.parse("2017-01-01 00:00:00"),
                     end_time=parser.parse("2017-01-01 05:00:00"),
                     clearing_price_filename="201701.csv",
                     previous_event_end=pd.Timestamp("01/01/2017 00:00:00"),
                     four_scenario_testing=False,
                     fleet_name="PVInverterFleet"):

        # Returns a Dictionary containing a month-worth of hourly SRMCP price data indexed by datetime.
        clearing_price_filename = join(dirname(abspath(__file__)), clearing_price_filename)
        self._clearing_price_helper.read_and_store_clearing_prices(clearing_price_filename, start_time)

        if not(four_scenario_testing):

            # Generate lists of 1-min request and response class objects.
            request_list_1m_tot, response_list_1m_tot = self.get_signal_lists(start_time, end_time)

            # Generate lists containing tuples of (timestamp, power) for request and response
            request_list_1m = [(r.ts_req, r.P_req / 1000) for r in request_list_1m_tot]
            request_df_1m = pd.DataFrame(request_list_1m, columns=['Date_Time', 'Request'])

            if 'battery' in fleet_name.lower():
                # Include battery SoC in response list for plotting purposes
                response_list_1m = [(r.ts, r.P_service / 1000, r.P_togrid, r.soc) for r in response_list_1m_tot]
                response_df_1m = pd.DataFrame(response_list_1m, columns=['Date_Time', 'Response', 'P_togrid', 'SoC'])
            else:
                response_list_1m = [(r.ts, r.P_service / 1000, r.P_togrid) for r in response_list_1m_tot]
                response_df_1m = pd.DataFrame(response_list_1m, columns=['Date_Time', 'Response', 'P_togrid'])
                
            # This merges/aligns the requests and responses dataframes based on their time stamp 
            # into a single dataframe
            df_1m = pd.merge(
                left=request_df_1m,
                right=response_df_1m,
                how='left',
                left_on='Date_Time',
                right_on='Date_Time')

            df_1m['P_togrid'] = df_1m['P_togrid'] / 100
            df_1m['P_base'] = df_1m['P_togrid'] - df_1m['Response']

            # Plot entire analysis period results and save plot to file
            # We want the plot to cover the entire df_1m dataframe
            plot_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'integration_test', 'reserve_service')
            ensure_ddir(plot_dir)
            plot_filename = datetime.now().strftime('%Y%m%d') + '_all_' + start_time.strftime('%B') + '_events_' + fleet_name + '.png'
            plt.figure(1)
            plt.figure(figsize=(15, 8))
            plt.subplot(211)
            if not(all(pd.isnull(df_1m['Request']))):
                plt.plot(df_1m.Date_Time, df_1m.Request, label='P_Request')
            if not(all(pd.isnull(df_1m['Response']))):
                plt.plot(df_1m.Date_Time, df_1m.Response, label='P_Response')
            if not(all(pd.isnull(df_1m['P_togrid']))):
                plt.plot(df_1m.Date_Time, df_1m.P_togrid, label='P_togrid')
            if not(all(pd.isnull(df_1m['P_base']))):
                plt.plot(df_1m.Date_Time, df_1m.P_base, label='P_base')
            plt.ylabel('Power (MW)')
            plt.legend(loc='best')
            if ('battery' in fleet_name.lower()) & (not(all(pd.isnull(df_1m['SoC'])))):
                plt.subplot(212)
                plt.plot(df_1m.Date_Time, df_1m.SoC, label='SoC')
                plt.ylabel('SoC (%)')
                plt.xlabel('Time')
            plt.savefig(join(plot_dir, plot_filename), bbox_inches='tight')
            plt.close()
        else: # Do this if we're running the 4-scenario tests
            df_1m = pd.read_excel(
                'test_fourscenarios_request_response.xlsx',
                infer_datetime_format=True)
            # Dummy values for plotting
            if 'battery' in fleet_name.lower():
                df_1m['SoC'] = 1.

        # Create empty data frame to store results in
        results_df = pd.DataFrame(columns=['Event_Start_Time', 'Event_End_Time',
            'Response_to_Request_Ratio', 'Response_MeetReqOrMax_Index_number',
            'Event_Duration_mins', 'Response_After10minToEndOr30min_To_First10min_Ratio',
            'Requested_MW', 'Responded_MW_at_10minOrEnd', 
            'Responded_MW_After10minToEndOr30min', 'Shortfall_Ratio',
            'Response_0min_Min_MW', 'Response_10minOrEnd_Max_MW',
            'Response_After10minToEnd_MW', 'Avg_Ramp_Rate', 'Best_Ramp_Rate',
            'SRMCP_DollarsperMWh_DuringEvent',
            'SRMCP_DollarsperMWh_SinceLastEvent',
            'Service_Value_NotInclShortfall_dollars',
            'Service_Value_InclShortfall_dollars',
            'Period_from_Last_Event_Hours',
            'Period_from_Last_Event_Days'])

        # Ensure that at least one event occurs within the specified time frame
        if df_1m.Request.sum() == 0:
            print('There are no events in the time frame you specified.')
            return [results_df, df_1m]
        else:
            # We can then do the following to break out the indices corresponding to events:
            # 1) np.where will return the dataframe indices where the request value is greater than 0
            # 2) np.split will split the array of indices from (1) into multiple arrays, each corresponding
            #    to a single event.  Here, we split the array from (1) based on where the difference between
            #    indices is greater than 1 (we assume that continuous indices correspond to the same event).
            event_indices = np.where(df_1m.Request > 0.)[0]
            event_indices_split = np.split(event_indices, np.where(np.insert(np.diff(event_indices), 0, 1) > 1)[0])

            # Then, we can take everything event-by-event.  "event_indices" contains the list of 
            # df_1m indices corresponding to a single event.
            for event_indices in event_indices_split:

                time_stamps_per_minute = 1 # each time stamp corresponds to a minute

                # Check if event is at least 11 minutes; if shorter, we'll need to add indices for
                # an extra minute at the end of the event
                shorter_than_11_min = ((df_1m.Date_Time[event_indices[len(event_indices) - 1]] - df_1m.Date_Time[event_indices[0]]).total_seconds() / 60.) < 11.

                # Create list of indices to add to start of event_indices representing the minute prior to the event starting
                # The np.arange call here creates a descending list of numbers, starting from the first index in event_indices
                # These numbers correspond to the extra indices we need to include for the -1 minute
                event_indices_prior_minute = [event_indices[0] - x for x in np.arange(time_stamps_per_minute, 0, -1)] 
                # Add the indices for the event prior to the event starting to the start of the event_indices list
                # np.insert will insert numbers into an array at the point you specify:
                # here, we want the number(s) to go at the start, signified by [0]*len(event_indices_prior_minute)
                event_indices_ready = np.insert(
                    event_indices,
                    [0] * len(event_indices_prior_minute),
                    event_indices_prior_minute)
                # If the event is shorter than 11 minutes, we want to account for an extra minute at the end
                if shorter_than_11_min:
                    # Now generate a list of indices to add to the end of event_indices_ready representing an extra minute
                    event_indices_after_minute = [event_indices[len(event_indices) - 1] + x for x in np.arange(1, time_stamps_per_minute + 1)]
                    # Append that extra minute's worth of indices to the end of event_indices_ready
                    event_indices_ready = np.append(event_indices_ready, event_indices_after_minute)

                # Filter the original dataframe down to just this event, including the minute prior to the event starting
                # and the minute after the event ends (if the event is shorter than 11 minutes)
                event = df_1m.loc[event_indices_ready, :]
                
                # Reset the event indices according to:
                # The negative first minute starts at index -1.0
                # The event's first minute starts at index 0.0
                event.index = np.arange(-time_stamps_per_minute, event.shape[0] - time_stamps_per_minute, 1 / time_stamps_per_minute)

                # Call the perf_metrics() method to obtain key event metrics
                performance_results = self.perf_metrics(event, shorter_than_11_min)

                # Call the event_value() method to calculate the event's value
                value_results = self.event_value(
                    Event_Start_Time=performance_results['Event_Start_Time'],
                    Event_End_Time=performance_results['Event_End_Time'],
                    Previous_Event_End_Time=previous_event_end,
                    Requested_MW=performance_results['Requested_MW'],
                    Responded_MW_at_10minOrEnd=performance_results['Responded_MW_at_10minOrEnd'],
                    Responded_MW_After10minToEndOr30min=performance_results['Responded_MW_After10minToEndOr30min'],
                    Shortfall_Ratio=performance_results['Shortfall_Ratio'])

                # Create temporary dataframe to contain the results
                event_results_df = pd.DataFrame({
                    'Event_Start_Time': performance_results['Event_Start_Time'],
                    'Event_End_Time': performance_results['Event_End_Time'],
                    'Response_to_Request_Ratio': performance_results['Response_to_Request_Ratio'],
                    'Response_MeetReqOrMax_Index_number': performance_results['Response_MeetReqOrMax_Index_number'],
                    'Event_Duration_mins': performance_results['Event_Duration_mins'],
                    'Response_After10minToEndOr30min_To_First10min_Ratio': performance_results['Response_After10minToEndOr30min_To_First10min_Ratio'],
                    'Requested_MW': performance_results['Requested_MW'],
                    'Responded_MW_at_10minOrEnd': performance_results['Responded_MW_at_10minOrEnd'],
                    'Responded_MW_After10minToEndOr30min': performance_results['Responded_MW_After10minToEndOr30min'],
                    'Shortfall_Ratio': performance_results['Shortfall_Ratio'],
                    'Response_0min_Min_MW': performance_results['Response_0min_Min_MW'],
                    'Response_10minOrEnd_Max_MW': performance_results['Response_10minOrEnd_Max_MW'],
                    'Response_After10minToEnd_MW': performance_results['Response_After10minToEnd_MW'],
                    'Avg_Ramp_Rate': performance_results['Avg_Ramp_Rate'],
                    'Best_Ramp_Rate': performance_results['Best_Ramp_Rate'],
                    'SRMCP_DollarsperMWh_DuringEvent': value_results['SRMCP_DollarsperMWh_DuringEvent'],
                    'SRMCP_DollarsperMWh_SinceLastEvent': value_results['SRMCP_DollarsperMWh_SinceLastEvent'],
                    'Service_Value_NotInclShortfall_dollars': value_results['Service_Value_NotInclShortfall_dollars'],
                    'Service_Value_InclShortfall_dollars': value_results['Service_Value_InclShortfall_dollars'],
                    'Period_from_Last_Event_Hours': value_results['Period_from_Last_Event_Hours'],
                    'Period_from_Last_Event_Days': value_results['Period_from_Last_Event_Days']},
                    index=[performance_results['Event_Start_Time']])

                # Append the temporary dataframe into the results_df
                results_df = pd.concat([results_df, event_results_df])
                # Plot event-specific results and save plot to file
                # We want the plot to start from the end of the previous event
                # and go until 10 minutes past the end of the current event
                plot_start = previous_event_end
                plot_end = performance_results['Event_End_Time'] + timedelta(minutes=10)
                plot_df = df_1m.loc[(df_1m.Date_Time >= plot_start) & (df_1m.Date_Time <= plot_end), :]
                plot_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'integration_test', 'reserve_service')
                plot_filename = datetime.now().strftime('%Y%m%d') + '_event_starting_' + performance_results['Event_Start_Time'].strftime('%Y%m%d-%H-%M') + '_' + fleet_name + '.png'
                plt.figure(1)
                plt.figure(figsize=(15, 8))
                plt.subplot(211)
                if not(all(pd.isnull(plot_df['Request']))):
                    plt.plot(plot_df.Date_Time, plot_df.Request, label='P_Request')
                if not(all(pd.isnull(plot_df['Response']))):
                    plt.plot(plot_df.Date_Time, plot_df.Response, label='P_Response')
                if not(all(pd.isnull(plot_df['P_togrid']))):
                    plt.plot(plot_df.Date_Time, plot_df.P_togrid, label='P_togrid')
                if not(all(pd.isnull(plot_df['P_base']))):
                    plt.plot(plot_df.Date_Time, plot_df.P_base, label='P_base')
                plt.ylabel('Power (MW)')
                plt.legend(loc='best')
                if ('battery' in fleet_name.lower()) & (not(all(pd.isnull(plot_df['SoC'])))):
                    plt.subplot(212)
                    plt.plot(plot_df.Date_Time, plot_df.SoC, label='SoC')
                    plt.ylabel('SoC (%)')
                    plt.xlabel('Time')
                if not(four_scenario_testing):
                    plt.savefig(join(plot_dir, plot_filename), bbox_inches='tight')
                plt.close()

                # Reset previous_end_end to be the end of this event before moving on to the next event
                previous_event_end = performance_results['Event_End_Time'] 

            return [results_df, df_1m]

    # Returns lists of requests and responses at 1m intervals.
    def get_signal_lists(self, start_time, end_time):
        # TODO: (minor) replace the temporary test file name with final event signal file name.
        historial_signal_filename = "gmlc_events_2017_1min.xlsx"
        # Returns a DataFrame that contains historical signal data in the events data file.
        historial_signal_filename = join(dirname(abspath(__file__)), historial_signal_filename)
        self._historial_signal_helper.read_and_store_historical_signals(historial_signal_filename)

        # Returns a Dictionary with datetime type keys.
        signals = self._historial_signal_helper.signals_in_range(start_time, end_time)

        sim_step = timedelta(minutes=1)
        requests = []
        responses = []

        # Call the "request" method to get 1-min responses in a list, requests are stored in a list as well.
        for timestamp, normalized_signal in signals.items():
            request, response = self.request(timestamp, sim_step, normalized_signal*self._fleet.assigned_service_kW())
            requests.append(request)
            responses.append(response)
        #print(requests)
        #print(responses)

        return requests, responses


    # Method for retrieving device fleet's response to each individual request.
    def request(self, ts, sim_step, p, q=0.0): # added input variables; what's the purpose of sim_step??
        fleet_request = FleetRequest(ts=ts, sim_step=sim_step, p=p, q=0.0)
        fleet_response = self.fleet.process_request(fleet_request)
        #print(fleet_response.P_service)
        return fleet_request, fleet_response


    def perf_metrics (self, event, shorter_than_11_min):
        '''
        '''
        # Obtain the start and end time stamps of the event
        Event_Start_Time = pd.Timestamp(event.Date_Time[0])
        Event_End_Time = pd.Timestamp(event.Date_Time.max())
        # Remove extra minute we added to the end if the original event was less than 11 minutes
        if shorter_than_11_min:
            Event_End_Time = Event_End_Time - timedelta(minutes = 1)
        # Calculate the event duration
        Event_Duration_mins = (Event_End_Time - Event_Start_Time).total_seconds() / 60.

        # Calculate event response at the start, which is the minimum response value
        # at the start, +/- 1 minute.  We already added in an extra minute before the event
        # started, so now we just take the minimum response
        # of the first three minutes of our data frame (minutes -1, 0, and 1).
        event_start_df = event.loc[:1, :]
        Response_0min_Min_MW = event_start_df.Response.min()

        # Calculate the requested MW for the event, which will be used in shortfall calculations
        # The requested value should be constant over the whole event, so the mean() call here shouldn't really matter
        Requested_MW = event.loc[event.Request > 0, 'Request'].mean()

        # Now calculate other metrics
        if not(shorter_than_11_min):
            # Calculate event response at the 10-minute mark, which is the maximum
            # response value from minutes 9, 10, and 11.
            event_end_10min_df = event.loc[9:11, :]
            Response_10minOrEnd_Max_MW = event_end_10min_df.Response.max()

            # Calculated responded MW
            Responded_MW_at_10minOrEnd = Response_10minOrEnd_Max_MW - Response_0min_Min_MW

            # Now calculate the response for the after 11-minute mark
            # This is the average response from 11 minutes on
            event_response_after11min_df = event.loc[11:, :]
            Response_After10minToEnd_MW = event_response_after11min_df.Response.mean()
            # Calculate ratio of response after 10 minutes to response at 10 minutes
            if Event_Duration_mins > 30:
                Responded_MW_After10minToEndOr30min = event.loc[11:30, :].Response.min() - Response_0min_Min_MW
                Response_After10minToEndOr30min_To_First10min_Ratio = event.loc[11:30, :].Response.min() / Response_10minOrEnd_Max_MW 
            else:
                Responded_MW_After10minToEndOr30min = event.loc[11:, :].Response.min() - Response_0min_Min_MW
                Response_After10minToEndOr30min_To_First10min_Ratio = event.loc[11:, :].Response.min() / Response_10minOrEnd_Max_MW   

            # Calculate shortfall ratio
            Shortfall_Ratio = min(Responded_MW_at_10minOrEnd, Responded_MW_After10minToEndOr30min) / Requested_MW        

        else:
            # Calculate the event response over the last 3 minutes of the event (including the additional
            # minute we already added on)
            event_end_df = event.iloc[-3:, :]
            Response_10minOrEnd_Max_MW = event_end_df.Response.max()

            # The event is shorter than 11 minutes, so return NaN for these two metrics
            Response_After10minToEnd_MW = np.nan
            Response_After10minToEndOr30min_To_First10min_Ratio = np.nan

            # Calculate the response ratio for the event
            # Calculate responded MW at 10 min mark or end of event
            Responded_MW_at_10minOrEnd = Response_10minOrEnd_Max_MW - Response_0min_Min_MW
            Responded_MW_After10minToEndOr30min = np.nan

            # Calculate shortfall ratio
            Shortfall_Ratio = Responded_MW_at_10minOrEnd / Requested_MW

        

        # Calculate response:request ratio
        Response_to_Request_Ratio = Responded_MW_at_10minOrEnd / Requested_MW

        # Calculate average ramp rate
        Avg_Ramp_Rate = Responded_MW_at_10minOrEnd / min(10, Event_Duration_mins)

        # Calculate best ramp rate
        if Response_to_Request_Ratio >= 1:
            try:
                # This will try to grab the event dataframe's index of the first time where the response matches (or exceeds) the request.
                # If no such index exists, skip down to the "except" call where the time to the max response will be
                # returned instead
                Response_MeetReqOrMax_Index_number = event.loc[(event.Date_Time >= Event_Start_Time) & (event.Response >= Requested_MW + Response_0min_Min_MW), :].index[0]
            except: 
                Response_Max_MW = event.loc[event.Date_Time >= Event_Start_Time, 'Response'].max()
                Response_MeetReqOrMax_Index_number = event.loc[event.Response == Response_Max_MW, :].index[0]
            Best_Ramp_Rate = Requested_MW / Response_MeetReqOrMax_Index_number
        else:
            Response_MeetReqOrMax_Index_number = min(10, Event_Duration_mins)
            Best_Ramp_Rate = Avg_Ramp_Rate

        return dict({
            'Event_Start_Time': Event_Start_Time,
            'Event_End_Time': Event_End_Time,
            'Response_to_Request_Ratio': Response_to_Request_Ratio,
            'Response_MeetReqOrMax_Index_number': Response_MeetReqOrMax_Index_number,
            'Event_Duration_mins': Event_Duration_mins,
            'Response_After10minToEndOr30min_To_First10min_Ratio': Response_After10minToEndOr30min_To_First10min_Ratio,
            'Requested_MW': Requested_MW,
            'Responded_MW_at_10minOrEnd': Responded_MW_at_10minOrEnd,
            'Responded_MW_After10minToEndOr30min': Responded_MW_After10minToEndOr30min,
            'Shortfall_Ratio': Shortfall_Ratio,
            'Response_0min_Min_MW': Response_0min_Min_MW,
            'Response_10minOrEnd_Max_MW': Response_10minOrEnd_Max_MW,
            'Response_After10minToEnd_MW': Response_After10minToEnd_MW,
            'Avg_Ramp_Rate': Avg_Ramp_Rate,
            'Best_Ramp_Rate': Best_Ramp_Rate})

    def event_value(self, Event_Start_Time, Event_End_Time, Previous_Event_End_Time,
                    Requested_MW, Responded_MW_at_10minOrEnd, 
                    Responded_MW_After10minToEndOr30min, Shortfall_Ratio,
                    hours_assigned_per_event_day=5, days_apart_each_assignment=5,
                    hours_assigned_on_each_bw_day=3):
        ''' Method to calculate an event's value, which is based on the requested MW for the event, the event duration,
        the event's shortfall (in MW), the time between the current event's end and the previous event's end, and
        the hourly price.
        '''
        # If event happens within a given day, the price is the average price over all hours of that day.
        # Otherwise, calculate weighted price based on the last half of the day the event started and
        # the first half of the day the event ended
        if Event_Start_Time.day == Event_End_Time.day:
            # get hourly keys for the day from the clearing prices dict
            hourly_price_keys_during_event = [x for x in self._clearing_price_helper.clearing_prices.keys() if x.date() == Event_Start_Time.date()]
        else:
            # get hourly keys for the last half of the start day and the first half of the end day from the clearing prices dict
            hourly_price_keys_during_event = [x for x in self._clearing_price_helper.clearing_prices.keys() if (x >= Event_Start_Time.replace(hour = 12).replace(minute = 0)) & (x <= Event_End_Time.replace(hour = 12).replace(minute = 0))]
        hourly_price_values_during_event = [self._clearing_price_helper.clearing_prices[x][0] for x in hourly_price_keys_during_event]
        SRMCP_DollarsperMWh_DuringEvent = np.mean(hourly_price_values_during_event)

        # Now calculate SRMCP since last event
        hourly_price_keys_sincelastevent = [x for x in self._clearing_price_helper.clearing_prices.keys() if (x >= Previous_Event_End_Time.replace(minute = 0)) & (x <= Event_Start_Time.replace(minute = 0))]
        hourly_price_values_sincelastevent = [self._clearing_price_helper.clearing_prices[x][0] for x in hourly_price_keys_sincelastevent]
        SRMCP_DollarsperMWh_SinceLastEvent = np.mean(hourly_price_values_sincelastevent)

        # Calculate the time between this event's end and the previous event's end (in hours)
        # This will be used to calculate the shortfall, if necessary
        Period_from_Last_Event_Hours = (Event_End_Time - Previous_Event_End_Time).total_seconds() / 3600.
        Period_from_Last_Event_Days = Period_from_Last_Event_Hours / 24.

        # Calculate value of event
        # Note in these calculations that Responded_MW_After10minToEndOr30min can be NaN.
        # Therefore, when we call the min() function for these equations, the first value
        # in the min() call must be Responded_MW_at_10minOrEnd, which will never be NaN
        # (otherwise, NaN could be returned for events shorter than 10 minutes).
        Service_Value_NotInclShortfall_dollars = (SRMCP_DollarsperMWh_DuringEvent *
                min(Responded_MW_at_10minOrEnd, Responded_MW_After10minToEndOr30min) *
                hours_assigned_per_event_day)
        if Shortfall_Ratio >= 1:
            Service_Value_InclShortfall_dollars = Service_Value_NotInclShortfall_dollars
        else:
            Shortfall_MW = Requested_MW - min(Responded_MW_at_10minOrEnd, Responded_MW_After10minToEndOr30min)
            Service_Value_InclShortfall_dollars = Service_Value_NotInclShortfall_dollars - (SRMCP_DollarsperMWh_SinceLastEvent * Shortfall_MW * Period_from_Last_Event_Hours / 24. / days_apart_each_assignment * hours_assigned_on_each_bw_day)
        return dict({
            'SRMCP_DollarsperMWh_DuringEvent': SRMCP_DollarsperMWh_DuringEvent,
            'SRMCP_DollarsperMWh_SinceLastEvent': SRMCP_DollarsperMWh_SinceLastEvent,
            'Service_Value_NotInclShortfall_dollars': Service_Value_NotInclShortfall_dollars,
            'Service_Value_InclShortfall_dollars': Service_Value_InclShortfall_dollars,
            'Period_from_Last_Event_Hours': Period_from_Last_Event_Hours,
            'Period_from_Last_Event_Days': Period_from_Last_Event_Days})

    # Use "dependency injection" to allow method "fleet" be used as an attribute.
    @property
    def fleet(self):
        return self._fleet

    @fleet.setter
    def fleet(self, value):
        self._fleet = value