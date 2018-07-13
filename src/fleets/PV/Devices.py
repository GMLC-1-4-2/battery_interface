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
    import Pre
    #import Weather
    import Mode_Selection
    import numpy as np
    from matplotlib import pyplot as plt
    import Limit_Check
    from scipy.signal import step
    
    Plot_MPP='Yes'
    time_step_minute=15

 #   [P_DirectS,Q_DirectS,PFS]=Direct_Control
    
    [Efficiency,Vdc,DC_Power,Rating,F_P,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
    [P_rated,P_min,S_max,Qmax_Plus,Qmax_minus]=Rating
    
    #[G_hr,T_hr]=Weather.Weather('yes')
    [DNI, Temp,Minute, Hour, Day_Target,Month_Target,Year_Target] \
        =Weather.Weather('yes')
    Direct_Control=Command_to_Device
    
    Auto_Direct_Mode=2
    Auto_Modes=1
    PF=1
    
    T_Stamp=[2017,1,28,14,30,00]
    [f,V]=Grid_Param()
    
    

    
    #[P_Pre,Pmpp_Pre,Q_Pre,P_req,Q_req,G_Pre,T_Pre]=Pre.OperatingPoint_Pre()
     #% intialization
    f_nom=60
     
  
    #% Please specify the length of duration 
#    [time_steps_seconds,time_steps_minutes,time_steps_hours]=Time_T
    
    
    
    #new_mode=1

    
    
     
    #Total_Iter=len(time_steps_seconds)*len(time_steps_minutes)*len(time_steps_hours)
    
    #P_rec=np.zeros(Total_Iter)
    #Q_rec=np.zeros(Total_Iter)
    #G_rec=np.zeros(Total_Iter)
    #T_rec=np.zeros(Total_Iter)
    #Time_=np.zeros(Total_Iter)
    #P_MPP=np.zeros(Total_Iter)

    
    #% [P_req,Q_req]=Mode_Selection(1,2,Pmpp_AC,P_Pre);
    #%Mode_Selection(Auto_Direct_Mode,Auto_Modes)
    #% Auto_Modes=1: frequency-watt
    #% Auto_Modes=2:  Volt-watt
    #% Auto_Modes=3: power factor
    #% Auto_Modes=4: volt-var 
    #% Auto_Direct_Mode=1: Autonomous mode
    #% Auto_Direct_Mode=2:  direct command mode
    Pmpp_AC=[]
    Q_max_available_Plus=[]
    Q_max_available_Minus=[]
    Time_=[]
    if return_forecast==True:
        Number_of_Forecasts=len(DNI)
        
        for i in range(Number_of_Forecasts):
            Pmpp_AC.append(MPP_Estimation.MPP_Estimation(DNI[i],Temp[i]))
            
            [Dummy,Q_max_available]=Limit_Check.Limit_Check(P_rated,Pmpp_AC[i],S_max,Pmpp_AC[i],Qmax_Plus,1)
            #Pmpp_AC.append(Pmpp_AC_)
            Q_max_available_Plus.append(Q_max_available)
            Q_max_available_Minus.append(-1*Q_max_available)
            Time_.append(Hour[i]+Minute[i]/60)
        #print(Pmpp_AC)    
        Forecast_Data=[Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus]
        import os
        File_Path=os.getcwd()+'\Forecast.npy'
        #import numpy as np
        np.save(File_Path,Forecast_Data)
        return Forecast_Data
        
        
        if Plot_MPP=='No':           
            fig, ax1 = plt.subplots()
            
            
            ax1.plot(Time_,Pmpp_AC, 'b-')
            ax1.set_xlabel('time (Hr)')
            # Make the y-axis label, ticks and tick labels match the line color.
            ax1.set_ylabel('Watt', color='b')
            ax1.tick_params('y', colors='b')
            ax1.legend(['Active Power'])
            s='Date: %g/%g/%g' %(Month_Target,Day_Target,Year_Target)
            
            
            ax2 = ax1.twinx()
            
            ax2.plot(Time_,Q_max_available_Plus,'r.')
            plt.hold(True)
            ax2.plot(Time_,Q_max_available_Minus,'r.')
            plt.hold(False)
            
            ax2.set_ylabel('VAR', color='r')
            ax2.tick_params('y', colors='r')
            ax2.legend(['Reactive Power'])
            ax2.text(.02, np.max(Q_max_available)-20, s, style='italic',
                    bbox={'facecolor':'red', 'alpha':0.5, 'pad':1})
            
            fig.tight_layout()
            plt.show()
            
    else:
        import numpy as np
        import os
        P_Output=[]
        Q_Output=[]
        Time_Current=[]
        File_Path_Forecast=os.getcwd()+'\Forecast.npy'
        File_Path_OperatingPoint=os.getcwd()+'\Operating_Point_Pre.npy'
        [Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus]=np.load(File_Path_Forecast)
        
        [P_Direct,Q_Direct]=Direct_Control
        [P_Grid,Q_Grid,P_Requested,Q_Requested]=np.load(File_Path_OperatingPoint)
        
        P_Pre=P_Grid
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
        P_Direct=get_iterable(P_Direct)
        Q_Direct=get_iterable(Q_Direct)
        
#%% calculate power
        #import datetime
        #now=datetime.datetime.now()
        #T_Stamp=[now.year,now.month,now.day,now.hour,now.minute,now.second]
        T_Stamp=ts
        
        for P_Command in P_Direct:
            Time_array=np.array(now)
            indx=P_Direct.index(P_Direct)
            Q_Command=Q_Direct[indx]
            Current_Forecast_indx=Match_Time(Time_,T_Stamp)
        
            P_Source_Max=Pmpp_AC[Current_Forecast_indx]#Maximum real power for services
            P_Min=0.0##Minimum real power for services
            Q_Max_Plus=Q_max_available_Plus[Current_Forecast_indx]#Maximum reactive power for services 
        #Q_Min_Plus=0#Minimum real power for services
            Q_Max_Minus=Q_max_available_Minus[Current_Forecast_indx]#Maximum reactive power for services 
        #Q_Min_Minus=0#Minimum real power for services
            P_Ramp_UP=1.0#Ramp rate real power up
            P_Ramp_Down=1.0#Ramp rate real power down
            Q_Ramp_UP=1.0#Ramp rate reactive power up
            Q_Ramp_Down=1.0#Ramp rate reactive power down
            P_Load=0.0
            P_Max=P_Source_Max-P_Load
        
        
            [P_Requested,Q_Requested]=Mode_Selection.Mode_Selection(Auto_Direct_Mode,Auto_Modes,P_Max,P_Pre,P_Command,Q_Command,PF,V,f,f_nom)
            if P_Requested<=P_Max and P_Requested>=P_Min:
                P_Output_Traget=P_Requested
            else:
                if P_Requested>P_Max:
                    P_Output_Traget=P_Max
                else:
                    P_Output_Traget=P_Min
            #P_Output=P_Output_Traget 
        
            [YYYY,M,D,hh,mm,ss]=T_Stamp
            T_Comapare=hh+mm/60
        #Time_Current.append(T_Comapare-.5)
        #print('P_Pre: %g' %P_Pre)
        #P_Output.append(P_Pre)

        #Time_Current.append(T_Comapare-.5)

        #for sec in range(5):
            h_times = np.arange(0.0, 5, 0.1)

#sys = signal.lti(1,[1,1.0/tau])

            step_response = F_P.step(T=h_times)[1]
        #plt.plot(h_times,step_response)
            #a=len(step_response)
#plt.plot(h_times, step_response/step_response.max())

#            [TT,P_F]=step(F_P,T=np.arange(0.,sec/10+.001,.1))
#            P_F=[0]+P_F
 #           print('TT')
#            TT
 
#            Multiplier=step_response[a]#            Time_Append=np.asarray(TT[-1])
#            print(Multiplier)
        #print('P_F')
        #print(P_F)
        #print('P_Pre')
        #print(P_Pre)
        #print('P_Output_Traget')
        #print(P_Output_Traget)
            P_Output_=[P_Pre+(P_Output_Traget-P_Pre)*x for x in step_response]
                
        #print('P_Pre: %g' %P_Pre)
        #print('P_Output_Traget: %g' %P_Output_Traget)
        #print('(P_Pre+(P_Output_Traget-P_Pre)): %g' %(P_Pre+(P_Output_Traget-P_Pre)))
        #plt.plot(h_times,step_response)
        
        #print('P_Output_ :%g' %len(P_Output_))
            
            #print('P_Output_: ')
            #P_Output_
        #print('P_Output_: %g' %P_Output_)
        #print('P_Output : %g' )
        #a=P_Output_[0]
            #for i in range(len(P_Output_)):
             #   P_Output.append(P_Output_[i])
            #Time_Current=[T_Comapare+x/3600 for x in h_times]
            
            #Time_Current.append(T_Comapare+.5)
            P_Output.append=P_Output_[-1]
        
        
        
            
        #print('a :%g' %a)
        #P_Output.append(P_Output_)
        #Time_Current.append(5)
        #print(P_Output)
        #print('%%')
#            if P_Output_<0:
#                P_Output_=0
        #print('P_Output_')
        #print(P_Output_)
        
        
#        plt.plot(P_Output)
        
 #       a=P_Output[-1]
#        print('a:%g' %a)
        #Time_Current.append(T_Comapare+.5)
        #P_Output.append(P_Output_)
        
#        [P_Output.append(x) for x in P_Output_]
        #[Time_Current.append(T_Comapare+x) for x in TT]
        #P_Output.insert(0,P_Grid)
        #print('%%%%%%')
        #print(P_Output)
       # print('%%%%%%')
        #print(Time_Current)
            
                
        if Q_Requested<=Q_Max_Plus and Q_Requested>=Q_Max_Minus:
            Q_Output_Traget=Q_Requested
        else:
            if Q_Requested>Q_Max_Plus:
                Q_Output_Traget=P_Max
            else:
                Q_Output_Traget=Q_Max_Minus
                
        Q_Output.append=Q_Output_Traget 
        
        P_GridBase=P_Max
        Q_GridBase=[Q_Max_Plus,Q_Max_Plus] 
        #print('%%')
        #P_Output.append(P_Pre)
        
        P_Grid=P_Output
#        print('P_Grid : %g' %P_Grid)
        P_Grid
        #print('%%')
        #P_Output.append(P_Pre)
        #Time_Current.append(T_Comapare-.5)
        Q_Grid=Q_Output
        
        Operating_Point_Pre=[P_Grid,Q_Grid,P_Requested,Q_Requested]
        
        #print(Operating_Point_Pre)
#        print('Operating_Point_Pre : %g' %Operating_Point_Pre)
        np.save(File_Path_OperatingPoint,Operating_Point_Pre)
        Device_Info=[P_Max,P_Min,Q_Max_Plus,Q_Max_Minus, \
                     P_Ramp_UP,P_Ramp_Down,Q_Ramp_UP,Q_Ramp_Down,P_Load, \
                     P_Output,Q_Output,P_GridBase,Q_GridBase,P_Grid,Q_Grid, \
                     P_Requested,Q_Requested,Time_Current]
        return Device_Info
        
    
            
#%%            
#        for h in time_steps_hours:
#            #% Retrieve modes for each hour
#            Auto_Direct_Mode=Auto_Direct_ModeS[h]
#            Auto_Modes=Auto_ModesS[h]
#            PF=PFS[h]
#            P_Direct=P_DirectS[h]
#            Q_Direct=Q_DirectS[h]
#            G=G_hr[h]
#            T=T_hr[h]
#            #new_mode=1
#            #print('\nHour   Minute    Second\n',h,'          0         0')   
#            for m in time_steps_minutes:
#                for sec in time_steps_seconds:               
#                    if G_Pre!=G or T_Pre!=T:
#                        Pmpp_AC=MPP_Estimation.MPP_Estimation(G,T)
#                        [Dummy,Q_max_available]=Limit_Check.Limit_Check(P_rated,Pmpp_AC,S_max,Pmpp_AC,Qmax_Plus,1)
#                        [P_req,Q_req]=Mode_Selection.Mode_Selection(Auto_Direct_Mode,Auto_Modes,Pmpp_AC,P_Pre,P_Direct,Q_Direct,PF,V,f,f_nom)
#                    if P_req!=P_Pre:
#                        [TT,P_F]=step(F_P,T=np.arange(0.,sec+.0001,.1))   
#                        P_F=[0]+P_F
#                        P=P_Pre+(P_req-P_Pre)*P_F[-1]
#                        if P<0:
#                            P=0
                        
#                    else: 
#                        P=P_Pre;           
#                    if Q_req!=Q_Pre:
#                        [TT,Q_F]=step(F_P,T=np.arange(0.,sec+.0001,.1))
#                        Q_F=[0]+Q_F
#                        Q=Q_Pre+(Q_req-Q_Pre)*Q_F[-1]
#                    else:
#                        Q=Q_Pre
#                    
#                    if Q_req!=Q_Pre or P_req!=P_Pre or Pmpp_Pre!=Pmpp_AC:
#                        [P,Q]=Limit_Check.Limit_Check(P_rated,Pmpp_AC,S_max,P,Q,1)
#                        
                   # print('\np req = '+str(P_req)+' Pmpp ='+str(Pmpp_AC)+' P deliverred ='+str(P))
                   
                   
                    #print(Q_req)
#                    P_rec.append(P)
#                    Q_rec.append(Q)
#                    G_rec.append(G)
#                    T_rec.append(T)
#                    Time_.append(h+m/60+sec/3600)
#                    P_MPP.append(Pmpp_AC)
#                    Q_Max.append(Q_max_available)
#                    P_req_.append(P_req)
#                    Q_req_.append(Q_req)
#                    counter=counter+1
#                P_Pre=P;
#                Q_Pre=Q;
#                Pmpp_Pre=Pmpp_AC;
#%%
                #print(Q_max_available)
            
    #        if Auto_Direct_Mode==1:
    #            Mode_A='Autonomous Mode';
    #            if Auto_Modes==1:
    #                Mode_B=': frequency-watt (Grid Frequency = '+ repr(f)+ ' Hz)'
    #            elif Auto_Modes==2:
    #                Mode_B=' :Volt-watt (Grid Voltage = ' +repr(V)+ ' p.u)'
    #            elif Auto_Modes==3:
    #                Mode_B=' :power factor (PF = '+ repr(PF) +')'
    #            else:
    #                Mode_B=' :Volt-Var(Grid Voltage = ' +repr(V)+ ' p.u)'
    #        else:
    #            Mode_A='Direct Control Mode';
    #            Mode_B=': Requested P = ' +repr(P_req) +' Watt and Requested Q = ' +repr(Q_req)+' Var'
        
            
    #        print(Mode_A +Mode_B)
    #        print('MPP = {}'.format(Pmpp_AC))
    #        print('Ative Power to grid = {0}  Watt and Reactive Power to Grid = {1} Var\n.'.format(P,Q))
        
        
        
        
        
        #fig, ax1 = plt.subplots()
        #ax1.plot(Time_, P_rec,Time_,Q_rec,Time_, P_req_,Time_,Q_req_,Time_,P_MPP, 'b-',[],[])
        #ax1.set_xlabel('V[V]')
        #ax1.legend(['P req','Q req','P_req_','Q_req_','P mpp'])
        
        #fig, ax1 = plt.subplots()
        #ax1.plot(Time_, G_rec, 'b-',[],[])
        #ax1.set_xlabel('Time (Hr)')
             #Make the y-axis label, ticks and tick labels match the line color.
        #ax1.set_ylabel('Irr', color='b')
        #ax1.tick_params('y', colors='b')
        #ax2 = ax1.twinx()
        #ax2.plot(Time_,T_rec, 'r')
        #ax2.set_ylabel('Temperature ($^0$C)', color='r')
        #ax2.tick_params('y', colors='r')
        
        
#        #%%
#        with open('Pre.py', 'r') as file:
#        # read a list of lines into data
#            data = file.readlines()
#        file.close
#    
#        data[10]=('    P_Pre={}\n'.format(P_rec[-1]))
#        data[11]=('    Pmpp_Pre={}\n'.format(P_MPP[-1]))
#        data[12]=('    Q_Pre={}\n'.format(Q_rec[-1]))
#        data[13]=('    P_req={}\n'.format(P_req_[-1]))
#        data[14]=('    Q_req={}\n'.format(Q_req_[-1]))
  #      data[15]=('    G_Pre={}\n'.format(G_rec[-1]))
  #      data[16]=('    T_Pre={}\n'.format(T_rec[-1]))
  #  
  #      with open('Pre.py', 'w') as file:
  #          file.writelines(data)
  #          
  #                  
  #      return Time_,P_rec,Q_rec,P_req_,Q_req_,P_MPP,Q_Max,G_rec,T_rec
        
    #% scatter(t,G,10,'fill')
    #% hold on
    #plot(Time_,P_rec,Time_,Q_rec,Time_,P_MPP,'*','LineWidth',2)
    #% xlim([min(time_steps_hours) max(time_steps_hours)])
    #legend('P','Q','P mpp')
    #xlabel('Time (Hr)')
    #% xlim([0,24])
    #% xticks([0 4 8 12 16 20 24])
    
    #figure
    #plot(Time_,G_rec,'*',Time_,T_rec,'LineWidth',2)
    #% hold on
    #legend('Irr','Temp')
    #xlabel('Time (Hr)')
    #% xlim([0,24])
    #% XTick([0 4 8 12 16 20 24])
    
    #% 
    #% [hAx,hLine1,hLine2] = plotyy(t,G,t,T);
    #% % ylabel(hAx(1),'Irradiance') % left y-axis
    #% ylabel(hAx(2),'Temperatore')
    #% xlim([0, 24])
    #%  ylim([0,1100])
