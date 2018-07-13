# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 10:45:48 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def Device_PV(ts,sim_step,Weather,Grid_Param,Command_to_Device,return_forecast):
    #Device_PV(Command_to_Device,Weather,Grid_Param,Request)
      #% Rating of the PV inverter, time response, weather information
    import MPP_Estimation
    import PV_Inverter_Data
    import Mode_Selection
    import numpy as np
    import Limit_Check
    import os
    import datetime
    
    
 #%% intialize data
 
 
    def datetime_from_utc_to_local(utc_datetime): # function to convert UTC time to local time
        from datetime import datetime
        import time
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
        return utc_datetime + offset  
    ts=datetime_from_utc_to_local(ts) #local time

    time_step_minute=sim_step.total_seconds()/60

    [Efficiency,Vdc,DC_Power,Rating,F_P,F_Q,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
    [P_rated,P_Min,S_max,Qmax_Plus,Qmax_minus]=Rating
    [P_up,P_down,Q_up,Q_down]=Ramp_Limit
    [DNI, Temp,Minute, Hour, Day_Target,Month_Target,Year_Target] \
        =Weather.Weather('yes')
    Direct_Control=Command_to_Device

    Auto_Direct_Mode=2
    Auto_Modes=1
    PF=1

    [f,V]=Grid_Param()

    f_nom=60


    Pmpp_AC=[]
    eff_mpp=[]
    Q_max_available_Plus=[]
    Q_max_available_Minus=[]
    Time_=[]
    #if return_forecast==True:
    Number_of_Forecasts=len(DNI)

    for i in range(Number_of_Forecasts):
        [Pmpp,eff]=MPP_Estimation.MPP_Estimation(DNI[i],Temp[i])
        Pmpp_AC.append(Pmpp)
        eff_mpp.append(eff)

        [Dummy,Q_max_available]=Limit_Check.Limit_Check(P_rated,Pmpp_AC[i],S_max,Pmpp_AC[i],Qmax_Plus,1)
            #Pmpp_AC.append(Pmpp_AC_)
        Q_max_available_Plus.append(Q_max_available)
        Q_max_available_Minus.append(-1*Q_max_available)
        Time_.append(Hour[i]+Minute[i]/60)
        #print(Pmpp_AC)
    Forecast_Data=[Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus]
    
    File_Path=os.getcwd()+'\Forecast.npy'
        #import numpy as np
    np.save(File_Path,Forecast_Data)

#%% Variable initiation
####################################################################
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#Battery-Equivalent API Variables Passed from the Device Fleet 
#to the High-Level Model (Step 4a) for the Time Step 

    P_grid=[]
    Q_grid=[]
    P_service=[]
    Q_service=[]
    E_t0=[]
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#.  Battery-Equivalent API Constraint Variables Passed from the Device Fleet 
#to the High-Level Model (Step 4b) for the Next Time Step

    c=[]
    P_output=[]
    Q_output=[]
    P_grid_max=[]
    Q_grid_max=[]
    P_grid_min=[]
    Q_grid_min=[]
    P_service_max=[]
    Q_service_max=[]
    P_service_min=[]
    Q_service_min=[]
    del_t_hold=[]
    t_restore=[]
    SP=[]
    N_req=[]
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#Other Battery-Equivalent Model’s Variables (Not Passed through the API)
    P_discharge=[]
    Q_discharge=[]
    P_grid_base=[]
    Q_grid_base=[]
    P_load=0
    P_load_base=0
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#Battery-Equivalent API Variables Passed from the High-Level Model to the Device Fleet
    P_req=[]
    Q_req=[]
    #Time_Current=[]
    
#%% Retrieve last operating status and forecast
    File_Path_Forecast=os.getcwd()+'\Forecast.npy'
    File_Path_OperatingPoint=os.getcwd()+'\Operating_Point_Pre.npy'
    [Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus]=np.load(File_Path_Forecast)

    [P_req,Q_req]=Direct_Control
    [P_Pre,Q_Pre,P_Requested,Q_Requested,Last_Time]=np.load(File_Path_OperatingPoint)
    #print("P_req = %d and Q_Pre ="%(P_req,Q_req))
    

    #P_Pre=P_Grid
    #Q_Pre=Q_Grid
    #P_Output.append(P_Pre)
    def Match_Time(Time_,T_Stamp):
        [YYYY,M,D,hh,mm,ss]=T_Stamp
        T_Comapare=hh+mm/60
        indx = (np.abs(Time_-T_Comapare)).argmin()
        return indx

    import collections
    def get_iterable(x):
        if isinstance(x, collections.Iterable):
            return x
        else:
            return (x,)
    P_req=get_iterable(P_req)
    Q_req=get_iterable(Q_req)
    #P_Load=0.0

#%% calculate power
    
    #now_=datetime.datetime.now()
    now_=ts

    Request_nos=np.max([len(P_req),len(Q_req)])
    if Request_nos==0:
        Request_nos=1

    for indx in range(Request_nos):
        now=now_

        date=np.array(now)
        T_Stamp=[now.year,now.month,now.day,now.hour,now.minute,now.second]
        #print(P_Command)
            #Time_array=np.array(now)
        #indx=P_req.index(P_Command)

        Current_Forecast_indx=Match_Time(Time_,T_Stamp)

        P_Source_Max=Pmpp_AC[Current_Forecast_indx]#Maximum real power for services

        Effeciency=eff_mpp[Current_Forecast_indx]
        P_grid_base.append(P_Source_Max-P_load)
        P_grid_base=get_iterable(P_grid_base)
        P_grid_max.append(P_Source_Max-P_load)
        P_grid_max=get_iterable(P_grid_max)
        P_service_max.append(P_grid_max[indx]-P_Min)
        P_service_max=get_iterable(P_service_max)
        
        P_grid_min.append(P_Min)
        P_grid_min=get_iterable(P_grid_min)
        P_service_min.append(0)
        P_service_min=get_iterable(P_service_min)
        
        #P_Min=0.0##Minimum real power for services
        Q_grid_max.append(Q_max_available_Plus[Current_Forecast_indx])#Maximum reactive power for services
        Q_grid_max=get_iterable(Q_grid_max)
        #Q_Min_Plus=0#Minimum real power for services
        Q_grid_min.append(Q_max_available_Minus[Current_Forecast_indx])#Maximum reactive power for services
        Q_grid_min=get_iterable(Q_grid_min)
        Q_service_max.append(Q_grid_max[indx]-Q_grid_min[indx])
        Q_service_max=get_iterable(Q_service_max)
        #Q_Min_Minus=0#Minimum real power for services

        
        #P_Max=P_Source_Max-P_Load
        try:
            P_Command=P_req[indx]
        except IndexError:
            P_Command=P_Source_Max
                
        try:
            Q_Command=Q_req[indx]
        except IndexError:
            Q_Command=0
            
           
            


        [P_Requested,Q_Requested]=Mode_Selection.Mode_Selection(Auto_Direct_Mode,Auto_Modes,P_grid_max[indx],P_Pre,P_Command,Q_Command,PF,V,f,f_nom)
        
        if P_Requested<=P_grid_max[indx] and P_Requested>=P_grid_min[indx]:
            P_Output_Traget=P_Requested
        else:
            if P_Requested>P_grid_max[indx]:
                P_Output_Traget=P_grid_max[indx]
            else:
                P_Output_Traget=P_grid_min[indx]
            #P_Output=P_Output_Traget


        if indx==0:
            time_step=now-Last_Time
            
            time_step=np.abs(time_step.total_seconds())
            h_times = np.arange(0.0, time_step, time_step/50)
        else:
            h_times = np.arange(0.0, time_step_minute*60, time_step_minute*60/50)


        step_response = F_P.step(T=h_times)[1]


        P_Pre=get_iterable(P_Pre)
        P_Pre=P_Pre[0]


        P_Output_=[P_Pre+(P_Output_Traget-P_Pre)*x for x in step_response]


        P_output.append(P_Output_[-1])
        P_output=get_iterable(P_output)

        if Q_Requested<=Q_grid_max[indx] and Q_Requested>=Q_grid_min[indx]:
            Q_Output_Traget=Q_Requested
        else:
            if Q_Requested>Q_grid_max[indx]:
                Q_Output_Traget=Q_grid_max[indx]
            else:
                Q_Output_Traget=Q_grid_min[indx]

        step_response = F_Q.step(T=h_times)[1]
        Q_Pre=get_iterable(Q_Pre)
        Q_Pre=Q_Pre[0]
        Q_Output_=[Q_Pre+(Q_Output_Traget-Q_Pre)*x for x in step_response]
        Q_output.append(Q_Output_[-1])
        Q_output=get_iterable(Q_output)
        
        if indx==0:
            P_grid=P_output[indx]
            Q_grid=Q_output[indx]
            P_service=P_grid_max[indx]-P_grid
            Q_service=Q_grid
            
        now_=now+datetime.timedelta(minutes=time_step_minute)
            




    Operating_Point_Pre=[P_grid,Q_grid,P_Requested,Q_Requested,now]
    
    date_=np.array(now_)
    date=np.append(date,date_)


    if return_forecast==False:
        np.save(File_Path_OperatingPoint,Operating_Point_Pre)
    Device_Info=[P_grid,Q_grid,P_service,Q_service,E_t0,c,P_output,Q_output,P_grid_max,Q_grid_max,\
                 P_grid_min,Q_grid_min,P_service_max,Q_service_max,P_service_min,Q_service_min,del_t_hold,\
                 t_restore,SP,N_req,Effeciency]
    return Device_Info

   