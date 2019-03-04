# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 13:26:26 2018

@author: rahosbach
"""

import pandas as pd
import numpy as np

def historic_events(interval_mins=1, year_min=2015, year_max=2017,
                    input_file_dir='C:\\Users\\rahosbach\\Downloads\\historical-spin-events.xls',
                    output_file_dir='C:\\Users\\rahosbach\\Documents\\GMLC_1.4.2\\'):
    print('Reading in raw events data.')
    raw_data = pd.read_excel(input_file_dir,
                             sheet_name='Events',
                             skiprows=4)
    # Parse out specific variables from the date
    raw_data['year'] = raw_data['Event Start'].apply(lambda x: x.year)
    raw_data['month'] = raw_data['Event Start'].apply(lambda x: x.month)
    raw_data['day_start'] = raw_data['Event Start'].apply(lambda x: x.day)
    raw_data['day_end'] = raw_data['Event End'].apply(lambda x: x.day)
    # Print the date as a string in YYYYMMDD format
    raw_data['monthdaydate'] = raw_data.apply(
            lambda row: (str(row.year) + ('0' if row.month < 10 else '') +
                         str(row.month) + ('0' if row.day_start < 10 else '') +
                         str(row.day_start)),
            axis=1)
    # Calculate start and end minutes (0-1440, based on entire day)
    raw_data['Minutes_Start'] = raw_data['Event Start'].apply(
            lambda x: x.hour * 60 + x.minute)
    raw_data['Minutes_End'] = raw_data['Event End'].apply(
            lambda x: x.hour * 60 + x.minute)
    
    # Confirm that there are no events that start on one day and end on 
    # the next
    print('Ensuring no events span multiple days.')
    try:
        raw_data.loc[raw_data.day_start != raw_data.day_end].shape[0] == 0
    except ValueError:
        print('Multi-day events are not properly being accounted for.')
        
    # Create list of minute intervals, starting at 0, ending at end of day
    minute_intervals = np.arange(start=0,
                                 stop=24*60,
                                 step=interval_mins,
                                 dtype='int')
      
    print('Creating empty results dataframe.')
    result_df = pd.DataFrame({
            'Minutes': minute_intervals})
    # add date columns that are filled with zero
    datecols = dict.fromkeys(
            pd.date_range('1/1/2017','12/31/2017').strftime('%m/%d/%Y'), 0)
    result_df = result_df.assign(**datecols)
    # Melt the date columns into rows (wide-to-long transformation)
    # This makes merging easier
    result_df_melted = pd.melt(
            result_df,
            id_vars=['Minutes'],
            var_name = 'Date',
            value_name = 'Value')
    
    for current_year in np.arange(year_min, year_max+1, 1):
    
        # Filter raw_data down to current_year and reset index after filtering
        raw_data_ready = raw_data.loc[(raw_data.year == current_year)]
        raw_data_ready.reset_index(drop=True,
                                   inplace=True)
        
        print('Readying event data for merging into results dataframe.')
        data_df = pd.DataFrame(columns=['Date', 'Minutes'])
        for row in np.arange(raw_data_ready.shape[0]):
            # Make all the dates have a year of 2017 and then print the dates
            # as strings
            ready_date = raw_data_ready.loc[row,
                                            'Event Start'].strftime('%m/%d/%Y')
            # Don't add one to the end of the range because the events end
            # right at the start of the second (meaning we don't need to
            # include the "Event End" second)
            minute_range = np.arange(raw_data_ready.loc[row, 'Minutes_Start'],
                                 raw_data_ready.loc[row, 'Minutes_End'])
            # np.digitize bins data based on bins you specify
            valid_intervals_indices = set(np.digitize(minute_range,
                                                      bins=minute_intervals,
                                                      right=False) - 1)
            # Get actual minute interval based on digitized indices
            minutes_ready = [minute_intervals[x] for x in \
                             valid_intervals_indices]
            # Create dataframe and add to data_df by row
            newdf = pd.DataFrame({
                    'Date': [ready_date] * len(minutes_ready),
                    'Minutes': minutes_ready})
            data_df = pd.concat([data_df, newdf], axis=0)
        data_df['Value'] = 1
        # Make sure minutes are integers for proper merging with
        # result_df_melted
        data_df.Minutes = data_df.Minutes.astype('int32')
        # Drop duplicate rows prior to merging, as they aren't needed and they
        # will cause issues
        data_df['CheckDups'] = data_df.apply(
                lambda row: str(row.Date) + str(row.Minutes),
                axis=1)
        data_df.drop_duplicates(subset='CheckDups',
                                keep='first',
                                inplace=True)
        data_df.drop('CheckDups',
                     axis=1,
                     inplace=True)
        
        print('Merging event data into results dataframe on time and date.')
        result_df_final = pd.merge(
                left = result_df_melted,
                right = data_df,
                how = 'left',
                left_on = ['Minutes', 'Date'],
                right_on = ['Minutes', 'Date'])
        print('Pivoting results dataframe from long to wide format.')
        result_df_final = result_df_final.pivot(
                index='Minutes',
                columns='Date',
                values='Value_y')
        print('Cleaning up results dataframe.')
        result_df_final.reset_index(level=0, inplace=True)
        result_df_final.Minutes = pd.to_datetime(
                result_df_final.Minutes,
                unit='m').dt.strftime('%H:%M:%S')
        result_df_final.fillna(0, inplace=True)
        result_df_final.rename(columns={'Minutes': ''},
                               inplace=True)
        print('Saving results dataframe to Excel file.')
        result_df_final.to_excel((output_file_dir +
                                 'gmlc_events_' +
                                 str(current_year) +
                                 '_' +
                                 str(interval_mins) +
                                 'min.xlsx'),
                                 index=False)
    
        
    
    
        
    
        
    
