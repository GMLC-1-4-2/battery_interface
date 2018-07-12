# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 14:50:48 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def Weather(Plot_Weather_Data):
    import csv    
    import numpy as np
    Year_Target=2017
    Day_Target = 31
    Month_Target=12
    
    File_Name='467381_39.73_-105.14_2015.csv'
    
    
    with open(File_Name, newline='') as csvfile:
        read_csv = csv.reader(csvfile, delimiter=' ', quotechar='|')
        rows_in_csv=[]
        for row in read_csv:
            rows_in_csv+=row
            
    rows_in_csv=rows_in_csv[82:]
    Year=[]
    Month=[]
    Day=[]
    Hour=[]
    Minute=[]
    DNI=[]
    Temp=[]
    Number_of_Entries=len(rows_in_csv)
    for i in range(Number_of_Entries):
        temp_row=rows_in_csv[i]
        Year.append(int(temp_row[0:temp_row.find(',')]))
        temp_row=temp_row[temp_row.find(',')+1:]
        Month.append(int(temp_row[0:temp_row.find(',')]))
        temp_row=temp_row[temp_row.find(',')+1:]
        Day.append(int(temp_row[0:temp_row.find(',')]))
        temp_row=temp_row[temp_row.find(',')+1:]
        Hour.append(int(temp_row[0:temp_row.find(',')]))
        temp_row=temp_row[temp_row.find(',')+1:]
        Minute.append(int(temp_row[0:temp_row.find(',')]))
        temp_row=temp_row[temp_row.find(',')+1:]
        DNI.append(float(temp_row[0:temp_row.find(',')]))
        temp_row=temp_row[temp_row.find(',')+1:] 
        Temp.append(float(temp_row[0:temp_row.find(',')]))
        
        
    
    np_array_Month = np.array(Month)  
    np_array_Day=np.array(Day) 
    #%% 
    item_index_Month = np.where(np_array_Month==Month_Target)
    item_index_Month=np.array(item_index_Month)
    Month_Search_Low_Index=item_index_Month[0,0]
    if Month_Target<12:
        item_index_Month = np.where(np_array_Month==Month_Target)
        item_index_Month=np.array(item_index_Month)
        Month_Search_Low_Index=item_index_Month[0,0]
        
        item_index_Month = np.where(np_array_Month==Month_Target+1)
        item_index_Month=np.array(item_index_Month)
        Month_Search_High_Index=item_index_Month[0,0]-1
    else:
        item_index_Month = np.where(np_array_Month==Month_Target)
        item_index_Month=np.array(item_index_Month)
        Month_Search_Low_Index=item_index_Month[0,0]
        Month_Search_High_Index=len(Month)
        
    Day=Day[Month_Search_Low_Index:Month_Search_High_Index]
    Hour=Hour[Month_Search_Low_Index:Month_Search_High_Index]
    Minute=Minute[Month_Search_Low_Index:Month_Search_High_Index]
    DNI=DNI[Month_Search_Low_Index:Month_Search_High_Index]
    Temp=Temp[Month_Search_Low_Index:Month_Search_High_Index]
    
    #%%
    item_index_Day = np.where(np_array_Day==Day_Target)
    item_index_Day=np.array(item_index_Day)
    Day_Search_Low_Index=item_index_Day[0,0]
    import calendar
    if Day_Target<calendar.monthrange(Year_Target,Month_Target)[1]:
     
        item_index_Day = np.where(np_array_Day==Day_Target+1)
        item_index_Day=np.array(item_index_Day)
        Day_Search_High_Index=item_index_Day[0,0]-1
    else:
        Day_Search_High_Index=len(Day)
        
    Day=Day[Day_Search_Low_Index:Day_Search_High_Index]
    Hour=Hour[Day_Search_Low_Index:Day_Search_High_Index]
    Minute=Minute[Day_Search_Low_Index:Day_Search_High_Index]
    DNI=DNI[Day_Search_Low_Index:Day_Search_High_Index]
    Temp=Temp[Day_Search_Low_Index:Day_Search_High_Index]
    
    Time_=[]
    for i in range(len(Hour)):
        Time_.append(Hour[i]+Minute[i]/60)
    #%%plot
    
    if Plot_Weather_Data=='no':
        import matplotlib.pyplot as plt
        
        fig, ax1 = plt.subplots()
        
        
        ax1.plot(Time_,DNI, 'b-')
        ax1.set_xlabel('time (Hr)')
        # Make the y-axis label, ticks and tick labels match the line color.
        ax1.set_ylabel('W/m2', color='b')
        ax1.tick_params('y', colors='b')
        ax1.legend(['Irradiance'])
        s='Date: %g/%g/%g' %(Month_Target,Day_Target,Year_Target)
        
        
        ax2 = ax1.twinx()
        
        ax2.plot(Time_,Temp, 'r.')
        ax2.set_ylabel('$^0$C', color='r')
        ax2.tick_params('y', colors='r')
        ax2.legend(['Temperature'])
        ax2.text(.02, np.max(Temp)-2, s, style='italic',
                bbox={'facecolor':'red', 'alpha':0.5, 'pad':1})
        
        fig.tight_layout()
        plt.show()
    
    return DNI, Temp,Minute, Hour, Day_Target,Month_Target,Year_Target