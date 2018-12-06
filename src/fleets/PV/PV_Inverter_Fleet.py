# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 11:07:32 2018

@author: rmahmud
"""

import sys
from os.path import dirname, abspath, join
sys.path.insert(0,dirname(dirname(dirname(abspath('__file__')))))

import configparser
import numpy  
import math
import collections
from scipy import signal
import numpy as np
import os
from datetime import datetime, timedelta

from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse



class PVInverterFleet(FleetInterface):
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """
    def __init__(self, GridInfo,**kwargs):
        """
        Constructor
        """

        
        self.is_P_priority = True
        self.is_autonomous = True
        self.autonomous_threshold = []

        # establish the grid locations that the battery fleet is conected to
        self.grid = GridInfo
        # Get cur directory
        base_path = dirname(abspath('__file__'))

        # Read config file
        self.config = configparser.ConfigParser()
        self.config.read(join(base_path, 'config.ini'))
        
        #%% initialize panel data
        self.PanelModel='M2453BB'
        Panel_Model='PV Panel Model: '+self.PanelModel
        self.iscn = float(self.config.get(Panel_Model, 'iscn'))
        self.vocn = float(self.config.get(Panel_Model, 'vocn'))
        self.imp = float(self.config.get(Panel_Model, 'imp'))
        self.vmp = float(self.config.get(Panel_Model, 'vmp'))
        self.pmax_e = float(self.config.get(Panel_Model, 'pmax_e'))
        self.kv =float(self.config.get(Panel_Model, 'kv'))
        self.ki = float(self.config.get(Panel_Model, 'ki'))
        self.ns =float(self.config.get(Panel_Model, 'ns'))
        
        
        #%% initialize PV inverter data
        self.InverterModel='ABB_MICRO_025'
        InverterModel='PV Inverter Model '+self.InverterModel
        self.qmax_plus = float(self.config.get(InverterModel, 'qmax_plus'))
        self.qmax_minus = float(self.config.get(InverterModel, 'qmax_minus'))
        self.p_rated = float(self.config.get(InverterModel, 'p_rated'))
        self.p_min = float(self.config.get(InverterModel, 'p_min'))
        self.s_max = float(self.config.get(InverterModel, 's_max'))
        self.a_p = float(self.config.get(InverterModel, 'a_p'))
        self.wn_p = float(self.config.get(InverterModel, 'wn_p'))
        self.tau_delay_p = float(self.config.get(InverterModel, 'tau_delay_p'))
        self.zeta_p = float(self.config.get(InverterModel, 'zeta_p'))
        self.p_ramp_up = float(self.config.get(InverterModel, 'p_ramp_up'))
        self.p_ramp_down = float(self.config.get(InverterModel, 'p_ramp_down'))
        self.q_ramp_up = float(self.config.get(InverterModel, 'q_ramp_up'))
        self.q_ramp_down = float(self.config.get(InverterModel, 'q_ramp_down'))
        cec_efficiency_chart_eff_row_1 = self.config.get(InverterModel, 'cec_efficiency_chart_eff_row_1')
        cec_efficiency_chart_eff_row_1_hold=cec_efficiency_chart_eff_row_1.split(',')
        self.cec_efficiency_chart_eff_row_1=[float(e) for e in cec_efficiency_chart_eff_row_1_hold]
        cec_efficiency_chart_eff_row_2 = self.config.get(InverterModel, 'cec_efficiency_chart_eff_row_2')
        cec_efficiency_chart_eff_row_2_hold=cec_efficiency_chart_eff_row_2.split(',')
        self.cec_efficiency_chart_eff_row_2=[float(e) for e in cec_efficiency_chart_eff_row_2_hold]
        cec_efficiency_chart_eff_row_3 = self.config.get(InverterModel, 'cec_efficiency_chart_eff_row_3')
        cec_efficiency_chart_eff_row_3_hold=cec_efficiency_chart_eff_row_3.split(',')
        self.cec_efficiency_chart_eff_row_3=[float(e) for e in cec_efficiency_chart_eff_row_3_hold]
        cec_efficiency_chart_ac_power = self.config.get(InverterModel, 'cec_efficiency_chart_ac_power')
        cec_efficiency_chart_ac_power_hold=cec_efficiency_chart_ac_power.split(',')
        self.cec_efficiency_chart_ac_power=[float(e) for e in cec_efficiency_chart_ac_power_hold]
        cec_efficiency_chart_vdc = self.config.get(InverterModel, 'cec_efficiency_chart_vdc')
        cec_efficiency_chart_vdc_hold=cec_efficiency_chart_vdc.split(',')
        self.cec_efficiency_chart_vdc=[float(e) for e in cec_efficiency_chart_vdc_hold]
        
        #%% subfleet data
        self.SubFleet='Sub Fleet'
        self.SubFleet_Name=self.config.get(self.SubFleet, 'SubFleet_Name')
        self.SubFleet_NumberOfUnits=float(self.config.get(self.SubFleet, 'SubFleet_NumberOfUnits'))
        self.SubFleet_InverterModel=self.config.get(self.SubFleet, 'SubFleet_InverterModel')
        self.SubFleet_PanelModel=self.config.get(self.SubFleet, 'SubFleet_PanelModel')
        
        self.num_of_devices=self.SubFleet_NumberOfUnits
        self.max_power_discharge=self.p_rated
        
        
        #%% Fleet data
        self.Fleet='Fleet'
        self.Fleet_Name=self.config.get(self.Fleet, 'Fleet_Name')
        self.Fleet_numberofsubfleets=float(self.config.get(self.Fleet, 'fleet_numberofsubfleets'))
        self.Fleet_InverterModel=self.config.get(self.Fleet, 'Fleet_InverterModel')
        self.Fleet_PanelModel=self.config.get(self.Fleet, 'Fleet_PanelModel')
        
        #%% Frequency-watt parameters
        FrequencyWatt='Frequency Watt'
        self.db_UF=float(self.config.get(FrequencyWatt,'db_UF'))
        self.db_OF=float(self.config.get(FrequencyWatt,'db_OF'))
        self.k_UF=float(self.config.get(FrequencyWatt,'k_UF'))
        self.k_OF=float(self.config.get(FrequencyWatt,'k_OF'))
        
        #%% Volt_var parameters
        VoltVar='Volt Var'
        self.delv1=float(self.config.get(VoltVar,'delv1'))
        self.Q1=float(self.config.get(VoltVar,'q1'))
        self.delv2=float(self.config.get(VoltVar,'delv2'))
        self.Q2=float(self.config.get(VoltVar,'q2'))
        self.delv3=float(self.config.get(VoltVar,'delv3'))
        self.Q3=float(self.config.get(VoltVar,'q3'))
        self.delv4=float(self.config.get(VoltVar,'delv4'))
        self.Q4=float(self.config.get(VoltVar,'q4'))
        
        #%% GridNominalCondition
  
        GridNominalCondition='Grid Nominal Condition'
        self.Vnom=float(self.config.get(GridNominalCondition,'Vnom'))
        self.fnom=float(self.config.get(GridNominalCondition,'fnom'))
        



        # Load config info with default values if there is no such config parameter in the config file
#        self.name = self.config.get(config_header, 'Name', fallback='Battery Inverter Fleet')
    def process_request(self, fleet_request):
        """
        This function takes the fleet request and repackages it for the interal run function
        :param fleet_request: an instance of FleetRequest
        :return fleet_response: an instance of FleetResponse
        """
        ts = fleet_request.ts_req
        dt = fleet_request.sim_step
        p_req = fleet_request.P_req
        q_req = fleet_request.Q_req
        # call run function with proper inputs
   
        fleet_response = self.Run_Fleet(ts=ts,sim_step=dt,P_req=p_req, Q_req=q_req, return_forecast=False,WP=self.is_P_priority)

        return fleet_response

    
    def forecast(self, requests):
#        responses = []
        ts = requests.ts_req
        dt = requests.sim_step
        p_req = requests.P_req
        q_req = requests.Q_req
#        for req in requests:
        FleetResponse = self.Run_Fleet(ts=ts,sim_step=dt,P_req=p_req, Q_req=q_req, return_forecast=True,WP=self.is_P_priority)
#                res = FleetResponse
#                responses.append(res)
        return FleetResponse
    
    def change_config(self, fleet_config):
        """
        This function updates the fleet configuration settings programatically.
        :param fleet_config: an instance of FleetConfig
        """

        # change config
        self.is_P_priority = fleet_config.is_P_priority
        self.is_autonomous = fleet_config.is_autonomous
        self.autonomous_threshold = fleet_config.autonomous_threshold

        pass
    

    def PV(self,G,T):
# The theory used in this program for modeling the PV device is found 
# in many sources in the litterature and is well explained in Chapter 1 of
#"Power Electronics and Control Techniques" by Nicola Femia, Giovanni 
# Petrone, Giovanni Spagnuolo and Massimo Vitelli. 

#        import math
#        import numpy
#        import matplotlib.pyplot as plt
                
        Iscn=self.iscn
        Vocn=self.vocn
        Imp=self.imp
        Vmp=self.vmp
        Pmax_e=self.pmax_e
        Kv=self.kv
        Ki=self.ki
        Ns=self.ns
           
        Gn = 1000               #Nominal irradiance [W/m^2] @ 25oC
        Tn = 25 + 273.15        #Nominal operating temperature [K]
        
        #Egap = 2.72370016e-19;  % Bandgap do silício amorfo em J (=1.7 eV)
        Egap = 1.8e-19          # Bandgap do silício cristalino em J (=1.124 eV)
        
        ns = Ns # for compatibility
        
        Ipvn = Iscn
        
        #G = 700
        T = T+273
        Ipv = Ipvn * G/Gn * (1 + Ki * (T-Tn))
        
        k = 1.3806503e-23   #%Boltzmann [J/K]
        q = 1.60217646e-19  #%Electron charge [C]
        
        Vt =  k*T /q
        Vtn = k*Tn/q
        
        a = (Kv - Vocn/Tn) / ( ns * Vtn * ( Ki/Ipvn - 3/Tn - Egap/(k*numpy.power(Tn,2) ) ))
        Ion=Ipvn /(math.exp(Vocn/(a*ns*Vtn))-1)
        C = Ion /  (numpy.power(Tn,3) * math.exp (-1*Egap / (k * Tn)))
        Io = C * numpy.power(Tn,3)* math.exp(-Egap/k/T)
        Rs = (a * ns * Vtn * math.log (1-Imp/Ipvn)+Vocn - Vmp)/Imp
        Rp = 9999999999 #% Rp = infinite
        
        # PROGRAM ENDS HERE
        
        
        #%% I-V and P-V CURVES of the calculated model at STC
        
        #% In this part of the program we are solving the I-V equation for several 
        #% (V,I) pairs and ploting the curves using the model previously calculated
        
        #% G =  700;               %Irradiance for evaluating the model 
        #% T =  25 + 273.15;        %Temperature for evaluating the model 
        
        #del V
        #del I
        
        nv = 50 #; % número de pontos da curva
        V=[]
        for x in range(nv):
            V.append(x*Vocn/nv) #V = 0:Vocn/nv:Vocn;  % Voltage vector
            
        I=[]
        g=[]
        glin=[]
        I_=[]
        for x in range(int(len(V))):
            I.append(0)
            g.append([])
            glin.append([])
            I_.append([])
        
        for j in range(int(len(V))):
            #g[j]=Ipv-Io*Ipv-Io*(math.exp((V[j])+I[j]*Rs)/Vt/ns/a)-1)-(V[j]+I[j]*Rs)/Rp-I[j];
            #print(V[j],I[j],end=' ')
            g[j]=(Ipv-Io*Ipv-Io*(math.exp((V[j]+I[j]*Rs)/(Vt*ns*a))-1)-(V[j]+I[j]*Rs)/Rp-I[j])
            while math.fabs(g[j])>.001:
                g[j]=(Ipv-Io*(math.exp((V[j]+I[j]*Rs)/Vt/ns/a)-1)-(V[j]+I[j]*Rs)/Rp-I[j])
                glin[j]=(-Io*Rs/Vt/ns/a*math.exp((V[j]+I[j]*Rs)/Vt/ns/a)-Rs/Rp-1)
                I_[j]=(I[j] - g[j]/glin[j])
                I[j]=I_[j]
              #  print(g[j],glin[j],I_[j],end=' ')
           
        #end
        for x in range(len(I)):
            if I[x]<0:
                I[x]=0
                
        P=[]
        for x in range(len(V)):
        #    if I[x]<0:
         #       I[x]=0
            P.append(I[x]*V[x])
            
            
            
      
        
        Pmpp=numpy.max(P)
        if Pmpp==0:
            Vmpp=Vocn
        else:    
            Vmpp=V[numpy.abs(P-numpy.max(P)).argmin()]
        
        return Pmpp,Vmpp
        
    
    
    def MPP_Estimation(self,G,T):
    
        

        import numpy
        from scipy.interpolate import interp1d
        
        
        [Pmpp,Vmpp]=self.PV(G,T)
        Efficiency=numpy.array([self.cec_efficiency_chart_eff_row_1,self.cec_efficiency_chart_eff_row_2,self.cec_efficiency_chart_eff_row_3])
        AC_Power=self.cec_efficiency_chart_ac_power
        Vdc=self.cec_efficiency_chart_vdc
        if isinstance(Vdc,list)==True:
            Vdc=numpy.array(Vdc)
        if isinstance(AC_Power,list)==True:
            AC_Power=numpy.array(AC_Power)
        if isinstance(Efficiency,list)==True:
            Efficiency=numpy.array(Efficiency)
        a=[]
        for x in range(3):
            a.append(AC_Power)
        DC_Power=numpy.divide(a,Efficiency/100)

        if Vmpp<Vdc[0]:
            Vmpp=Vdc[0]+.1
       
     
        if numpy.abs(Vdc-Vmpp).argmin()<len(Vdc):
            x=DC_Power[numpy.abs(Vdc-Vmpp).argmin(),:]
            y=Efficiency[numpy.abs(Vdc-Vmpp).argmin(),:]
            f1= interp1d(x, y)
            
          
            x=DC_Power[numpy.abs(Vdc-Vmpp).argmin()+1,:]
            y=Efficiency[numpy.abs(Vdc-Vmpp).argmin()+1,:]
            f2= interp1d(x, y)
          
            pos=numpy.abs(Vdc-Vmpp).argmin()
            eff_mpp=f1(Vmpp)+(f1(Vmpp)-f2(Vmpp))*(Vdc[pos]-Vmpp)/(Vdc[pos]-Vdc[pos+1])
            
        else:
            x=DC_Power[numpy.abs(Vdc-Vmpp).argmin(),:]
            y=Efficiency[numpy.abs(Vdc-Vmpp).argmin(),:]
            f1= interp1d(x, y)
            x=DC_Power[numpy.abs(Vdc-Vmpp).argmin()-1,:]
            y=Efficiency[numpy.abs(Vdc-Vmpp).argmin()-1,:]
            f2= interp1d(x, y)
            pos=numpy.abs(Vdc-Vmpp).argmin()
            eff_mpp=f1(Vmpp)+(f1(Vmpp)-f2(Vmpp))*(Vdc[pos]-Vmpp)/(Vdc[pos]-Vdc[pos])
            
        if Pmpp==0:
            Pmpp_AC=0
        else:
            Pmpp_AC=Pmpp*eff_mpp/100
            
        return Pmpp_AC,eff_mpp   
    
    
    def Limit_Check(self,P_rated,Pmpp_AC,S_max,P,Q,WP):
        import numpy as np
        
        if P>np.minimum(P_rated,Pmpp_AC):
            P=np.minimum(P_rated,Pmpp_AC)
        
        S=np.sqrt(np.power(P,2)+np.power(Q,2));
        if S>S_max:
            if WP==True:#%watt priority
                Q=np.sqrt(np.power(S_max,2)-np.power(P,2))
            else:# % var priority
                P=np.sqrt(np.power(S_max,2)-np.power(Q,2))
                
    
        return P,Q  
    
    
    def Device_PV(self,ts,sim_step,Command_to_Device,return_forecast,WP):
    #Device_PV(Command_to_Device,Weather,Grid_Param,Request)
      #% Rating of the PV inverter, time response, weather information

        import numpy as np
        import os
        import datetime

        
        #%% intialize data
     
     

        ts=self.datetime_from_utc_to_local(ts) #local time
    
        time_step_minute=sim_step.total_seconds()/60
    
        
        P_rated=self.p_rated
        P_Min=self.p_min
        S_max=self.s_max
        Qmax_Plus=self.qmax_plus

        
        
        num=[self.wn_p*self.wn_p]
        den=[self.a_p, 2*self.zeta_p*self.wn_p, self.wn_p*self.wn_p]
        F_P=signal.TransferFunction(num, den)
        F_Q=signal.TransferFunction(num, den)

        
        
        [DNI, Temp,Minute, Hour, Day_Target,Month_Target,Year_Target] \
            =self.Weather('no')
        Direct_Control=Command_to_Device

    

        
        if return_forecast==True:
            Pmpp_AC=[]
            eff_mpp=[]
            Q_max_available_Plus=[]
            Q_max_available_Minus=[]
            Time_=[]
            #if return_forecast==True:
            Number_of_Forecasts=len(DNI)
        
            for i in range(Number_of_Forecasts):
                [Pmpp,eff]=self.MPP_Estimation(DNI[i],Temp[i])
                Pmpp_AC.append(Pmpp)
                eff_mpp.append(eff)
        
                [Dummy,Q_max_available]=self.Limit_Check(P_rated,Pmpp_AC[i],S_max,Pmpp_AC[i],Qmax_Plus,WP)
                    #Pmpp_AC.append(Pmpp_AC_)
                Q_max_available_Plus.append(Q_max_available)
                Q_max_available_Minus.append(-1*Q_max_available)
                Time_.append(Hour[i]+Minute[i]/60)
                #print(Pmpp_AC)
            Forecast_Data=[Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus,eff_mpp]
            
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
        Effeciency=[]
    #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
    #Other Battery-Equivalent Model’s Variables (Not Passed through the API)

        P_grid_base=[] 
        P_load=0
    #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
    #Battery-Equivalent API Variables Passed from the High-Level Model to the Device Fleet
        P_req=[]
        Q_req=[]
        #Time_Current=[]
        
            #%% Retrieve last operating status and forecast
        File_Path_Forecast=os.getcwd()+'\Forecast.npy'
        File_Path_OperatingPoint=os.getcwd()+'\Operating_Point_Pre.npy'
        [Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus,eff_mpp]=np.load(File_Path_Forecast)
    
        [P_req,Q_req]=Direct_Control
        
        #print("P_req = %d and Q_Pre ="%(P_req,Q_req))
        
    
        #P_Pre=P_Grid
        #Q_Pre=Q_Grid
        #P_Output.append(P_Pre)

    

        P_req=self.get_iterable(P_req)
        Q_req=self.get_iterable(Q_req)
        #P_Load=0.0
    
            #%% calculate power
        
        #now_=datetime.datetime.now()
        now_=ts
    
        Request_nos=np.max([len(P_req),len(Q_req)])
        if Request_nos==0:
            Request_nos=1
    
        for indx in range(Request_nos):
            [P_Pre,Q_Pre,P_Requested,Q_Requested,Last_Time]=np.load(File_Path_OperatingPoint)
            now=now_
            #print('now = ',now)
    
            date=np.array(now)
            T_Stamp=[now.year,now.month,now.day,now.hour,now.minute,now.second]
            #print(P_Command)
                #Time_array=np.array(now)
            #indx=P_req.index(P_Command)
    
            Current_Forecast_indx=self.Match_Time(Time_,T_Stamp)
    
            P_Source_Max=Pmpp_AC[Current_Forecast_indx]#Maximum real power for services
            #print('P_Source_Max =',P_Source_Max)
    
            Effeciency.append(eff_mpp[Current_Forecast_indx])
            P_grid_base.append(P_Source_Max-P_load)
            P_grid_base=self.get_iterable(P_grid_base)
            P_grid_max.append(P_Source_Max-P_load)
            P_grid_max=self.get_iterable(P_grid_max)
            P_service_max.append(P_grid_max[indx]-P_Min)
            P_service_max=self.get_iterable(P_service_max)
            

            
            P_grid_min.append(P_Min)
            P_grid_min=self.get_iterable(P_grid_min)
            P_service_min.append(0)
            P_service_min=self.get_iterable(P_service_min)
            
            #P_Min=0.0##Minimum real power for services
            Q_grid_max.append(Q_max_available_Plus[Current_Forecast_indx])#Maximum reactive power for services
            Q_grid_max=self.get_iterable(Q_grid_max)
            #Q_Min_Plus=0#Minimum real power for services
            Q_grid_min.append(Q_max_available_Minus[Current_Forecast_indx])#Maximum reactive power for services
            Q_grid_min=self.get_iterable(Q_grid_min)
            Q_service_max.append(Q_grid_max[indx]-Q_grid_min[indx])
            Q_service_max=self.get_iterable(Q_service_max)
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
                
               
                
    
    
    #        [P_Requested,Q_Requested]=Mode_Selection.Mode_Selection(Auto_Direct_Mode,Auto_Modes,P_grid_max[indx],P_Pre,P_Command,Q_Command,PF,V,f,f_nom)
            P_Requested=P_Command
            Q_Requested=Q_Command
#            print('P_Requested =',P_Requested)
#            print('Q_Requested =',Q_Requested)
            #print('P_Requested=',P_Requested,' P_grid_max[indx] = ',P_grid_max[indx],' P_grid_min[indx] = ',P_grid_min[indx])
            
            if P_Requested<=P_grid_max[indx] and P_Requested>=P_grid_min[indx]:
                P_Output_Traget=P_Requested
            else:
                if P_Requested>P_grid_max[indx]:
                    P_Output_Traget=P_grid_max[indx]
                else:
                    P_Output_Traget=P_grid_min[indx]
                #P_Output=P_Output_Traget
                
            if Q_Requested<=Q_grid_max[indx] and Q_Requested>=Q_grid_min[indx]:
                Q_Output_Traget=Q_Requested
            else:
                if Q_Requested>Q_grid_max[indx]:
                    Q_Output_Traget=Q_grid_max[indx]
                else:
                    Q_Output_Traget=Q_grid_min[indx]
                
            
            [P_Output_Traget,Q_Output_Traget]=self.Limit_Check(P_rated,P_grid_max[indx],S_max,P_Output_Traget,Q_Output_Traget,WP)

    
            if indx==0:
                time_step=now-Last_Time
#                print(now)
#                print(Last_Time)
#                print(time_step)
                time_step=np.abs(time_step.total_seconds())
                h_times = np.arange(0.0, time_step, time_step/50)
            else:
                h_times = np.arange(0.0, time_step_minute*60, time_step_minute*60/50)
                
#            print(h_times)
    
    
            step_response = F_P.step(T=h_times)[1]
    
    
            P_Pre=self.get_iterable(P_Pre)
            P_Pre=P_Pre[0]
    
    
            P_Output_=[P_Pre+(P_Output_Traget-P_Pre)*x for x in step_response]
    
    
            P_output.append(P_Output_[-1])
            P_output=self.get_iterable(P_output)
    
    
    
            step_response = F_Q.step(T=h_times)[1]
            Q_Pre=self.get_iterable(Q_Pre)
            Q_Pre=Q_Pre[0]
            Q_Output_=[Q_Pre+(Q_Output_Traget-Q_Pre)*x for x in step_response]
            Q_output.append(Q_Output_[-1])
            Q_output=self.get_iterable(Q_output)
            
            if indx==0:
                P_grid=P_output[indx]
                Q_grid=Q_output[indx]
                P_service=P_grid_max[indx]-P_grid
                Q_service=Q_grid
                
            now_=now+datetime.timedelta(minutes=time_step_minute)
            
#            print('P_grid = ',P_grid)
#            print('Q_grid = ',Q_grid)
            Operating_Point_Pre=[P_grid,Q_grid,P_Requested,Q_Requested,now]
                
            if return_forecast==False:
                np.save(File_Path_OperatingPoint,Operating_Point_Pre)
                #print('Operating_Point_Pre',Operating_Point_Pre)
                
            date_=np.array(now_)
            date=np.append(date,date_)
            #print('P_grid=',P_grid,'P_Output_Traget =',P_Output_Traget,'P_Requested = ',P_Requested)
                
                
                
        Device_Info=[P_grid,Q_grid,P_service,Q_service,E_t0,c,P_output,Q_output,P_grid_max,Q_grid_max,\
                     P_grid_min,Q_grid_min,P_service_max,Q_service_max,P_service_min,Q_service_min,del_t_hold,\
                     t_restore,SP,N_req,Effeciency]
        return Device_Info
    
    
    def datetime_from_utc_to_local(self,utc_datetime): # function to convert UTC time to local time
            from datetime import datetime
            import time
            now_timestamp = time.time()
            offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
            return utc_datetime + offset  
    def Match_Time(self,Time_,T_Stamp):
            [YYYY,M,D,hh,mm,ss]=T_Stamp
            T_Comapare=hh+mm/60
            indx = (numpy.abs(Time_-T_Comapare)).argmin()
            return indx  
                
    def get_iterable(self,x):
            if isinstance(x, collections.Iterable):
                return x
            else:
                return (x,)
    
    def Weather(self,Plot_Weather_Data):
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
        
        if Plot_Weather_Data=='yes':
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
    
 
    
    def Run_Fleet(self,ts,sim_step,P_req, Q_req, return_forecast,WP): 
 # this module aggregates the PV information from a large pool of PV/invertre system
# Updates prepares report for system operator based on PV fleet
# Breaks down the operation command from system operator to subfleet and device level   

        if P_req==None:
            P_req=[]
        if Q_req==None:
            Q_req=[]
        
        
        
    
        
        def Grid_Param():
            from grid_info import GridInfo
            a=GridInfo()
            V=a.get_voltage('XX')
            f=a.get_frequency('XX')
            return f, V
        
    # pull information about the PV subfleet
        P_rated=self.p_rated
        P_min=self.p_min
        S_max=self.s_max
        Qmax_Plus=self.qmax_plus
        Qmax_minus=self.qmax_minus
        P_up=self.p_ramp_down
        P_down=self.p_ramp_down
        Q_up=self.q_ramp_down
        Q_down=self.q_ramp_down
        
    
       
    # Create Battery equivalent model (BEM) variables for the subfleets and PV fleet    

#        SubFleetA_NP_C='NA'          
#        SubFleetA_NP_P_grid_max=P_rated*self.SubFleet_NumberOfUnits #Minimum real power for services
#        SubFleetA_NP_Q_grid_max=Qmax_Plus*self.SubFleet_NumberOfUnits#Maximum reactive power for services 
#        SubFleetA_NP_P_grid_min=P_min*self.SubFleet_NumberOfUnits#Minimum reactive power for services 
#        SubFleetA_NP_Q_grid_min=Qmax_minus*self.SubFleet_NumberOfUnits#Ramp rate real power up
#        SubFleetA_NP_P_service_max=SubFleetA_NP_P_grid_max-SubFleetA_NP_P_grid_min#Ramp rate real power down
#        SubFleetA_NP_Q_service_max=SubFleetA_NP_Q_grid_max-SubFleetA_NP_Q_grid_min#Ramp rate reactive power up
#        SubFleetA_NP_P_service_min=0#Ramp rate reactive power down
#        SubFleetA_NP_Q_service_min=0
        SubFleetA_NP_P_up=P_up
        SubFleetA_NP_Q_up=Q_up
        SubFleetA_NP_P_down=P_down
        SubFleetA_NP_Q_down=Q_down
#        SubFleetA_NP_e_in='NA'
        SubFleetA_NP_e_out=[]
        SubFleetA_NP_S_rating=S_max*self.SubFleet_NumberOfUnits
    

        Fleet_PV_NP_C='NA'          
#        Fleet_PV_NP_P_grid_max=SubFleetA_NP_P_grid_max#Minimum real power for services
#        Fleet_PV_NP_Q_grid_max=SubFleetA_NP_Q_grid_max#Maximum reactive power for services 
#        Fleet_PV_NP_P_grid_min=SubFleetA_NP_P_grid_min#Minimum reactive power for services 
#        Fleet_PV_NP_Q_grid_min=SubFleetA_NP_Q_grid_min#Ramp rate real power up
#        Fleet_PV_NP_P_service_max=SubFleetA_NP_P_service_max#Ramp rate real power down
#        Fleet_PV_NP_Q_service_max=SubFleetA_NP_Q_service_max#Ramp rate reactive power up
#        Fleet_PV_NP_P_service_min=0#Ramp rate reactive power down
#        Fleet_PV_NP_Q_service_min=0
        Fleet_PV_NP_P_up=SubFleetA_NP_P_up
        Fleet_PV_NP_Q_up=SubFleetA_NP_Q_up
        Fleet_PV_NP_P_down=SubFleetA_NP_P_down
        Fleet_PV_NP_Q_down=SubFleetA_NP_Q_down
        Fleet_PV_NP_e_in='NA'
#        Fleet_PV_NP_e_out=[]
        FleetA_NP_S_rating=SubFleetA_NP_S_rating
        
       # break down the command for fleet to command for device  
        Command_to_Device=self.Aggregator_Command(P_req, Q_req,self.SubFleet_NumberOfUnits)
                
            # Grid parameters required for autonomous mode of operation
           
            
            #[Time_,P_rec,Q_rec,P_req_,Q_req_,P_MPP,G_rec,T_rec]\
        [P_grid,Q_grid,P_service,Q_service,E_t0,c,P_output,Q_output,P_grid_max,Q_grid_max,\
             P_grid_min,Q_grid_min,P_service_max,Q_service_max,P_service_min,Q_service_min,del_t_hold,\
             t_restore,SP,N_req,Effeciency]=self.Device_PV(ts,sim_step,Command_to_Device,return_forecast,WP)
      
            #print(P_Output)    
        SubFleetA_P_grid=P_grid*self.SubFleet_NumberOfUnits
        SubFleetA_Q_grid=Q_grid* self.SubFleet_NumberOfUnits
        SubFleetA_P_service=P_service* self.SubFleet_NumberOfUnits
        SubFleetA_Q_service=Q_service* self.SubFleet_NumberOfUnits
        SubFleetA_E_t0=E_t0
        SubFleetA_c=c
        SubFleetA_P_output=[x*self.SubFleet_NumberOfUnits for x in P_output]
        SubFleetA_Q_output=[x*self.SubFleet_NumberOfUnits for x in Q_output]
        SubFleetA_P_grid_max=[x*self.SubFleet_NumberOfUnits for x in P_grid_max]
        SubFleetA_Q_grid_max=[x*self.SubFleet_NumberOfUnits for x in Q_grid_max]
        SubFleetA_P_grid_min=[x*self.SubFleet_NumberOfUnits for x in P_grid_min]
        SubFleetA_Q_grid_min=[x*self.SubFleet_NumberOfUnits for x in Q_grid_min]
        SubFleetA_P_service_max=[x*self.SubFleet_NumberOfUnits for x in P_service_max]
        SubFleetA_Q_service_max=[x*self.SubFleet_NumberOfUnits for x in Q_service_max]
        SubFleetA_P_service_min=[x*self.SubFleet_NumberOfUnits for x in P_service_min]
        SubFleetA_Q_service_min=[x*self.SubFleet_NumberOfUnits for x in Q_service_min]
        SubFleetA_del_t_hold=del_t_hold
        SubFleetA_t_restore=t_restore
        SubFleetA_SP=SP
        SubFleetA_N_req=N_req
        SubFleetA_NP_e_out=Effeciency
        
        # Calculate information about Subfleets    
        
        # Calculate information about Device Fleet: PV
        # Calculate information about Subfleets    
        Fleet_PV_P_grid=SubFleetA_P_grid
        Fleet_PV_Q_grid=SubFleetA_Q_grid
        Fleet_PV_P_service=SubFleetA_P_service
        Fleet_PV_Q_service=SubFleetA_Q_service
        Fleet_PV_E_t0=SubFleetA_E_t0
#        Fleet_PV_c=SubFleetA_c
#        
#        Fleet_PV_P_output=SubFleetA_P_output
#        Fleet_PV_Q_output=SubFleetA_Q_output
        Fleet_PV_P_grid_max=SubFleetA_P_grid_max
        Fleet_PV_Q_grid_max=SubFleetA_Q_grid_max
        Fleet_PV_P_grid_min=SubFleetA_P_grid_min
        Fleet_PV_Q_grid_min=SubFleetA_Q_grid_min
        Fleet_PV_P_service_max=SubFleetA_P_service_max
        Fleet_PV_Q_service_max=SubFleetA_Q_service_max
        Fleet_PV_P_service_min=SubFleetA_P_service_min
        Fleet_PV_Q_service_min=SubFleetA_Q_service_min
        Fleet_PV_del_t_hold=SubFleetA_del_t_hold
        Fleet_PV_t_restore=SubFleetA_t_restore
#        Fleet_PV_SP=SubFleetA_SP
#        Fleet_PV_N_req=SubFleetA_N_req
        
        
        
        response = FleetResponse()
        response.ts = ts
        response.C=Fleet_PV_NP_C
        response.dT_hold_limit=Fleet_PV_del_t_hold
        response.E=Fleet_PV_E_t0
        response.Eff_charge=Fleet_PV_NP_e_in
        response.Eff_discharge=SubFleetA_NP_e_out
        response.P_dot_down=Fleet_PV_NP_P_down
        response.P_dot_up=Fleet_PV_NP_P_up
        response.P_service=Fleet_PV_P_service
        response.P_service_max=Fleet_PV_P_service_max
        response.P_service_min=Fleet_PV_P_service_min
        response.P_togrid=Fleet_PV_P_grid
        response.P_togrid_max=Fleet_PV_P_grid_max[0]
        response.P_togrid_min=Fleet_PV_P_grid_min[0]
        response.Q_dot_down=Fleet_PV_NP_Q_down
        response.Q_dot_up=Fleet_PV_NP_Q_up
        response.Q_service=Fleet_PV_Q_service
        response.Q_service_max=Fleet_PV_Q_service_max
        response.Q_service_min=Fleet_PV_Q_service_min
        response.Q_togrid=Fleet_PV_Q_grid
        response.Q_togrid_max=Fleet_PV_Q_grid_max[0]
        response.Q_togrid_min=Fleet_PV_Q_grid_min[0]
        response.S_Rating=FleetA_NP_S_rating
        response.T_restore=Fleet_PV_t_restore
        return response


    def Aggregator_Command(self,P_DirectS, Q_DirectS,Scaling):
    
    # breaks down the command for aggregator to command for device

       
        P_DirectS=self.get_iterable(P_DirectS)
        Q_DirectS=self.get_iterable(Q_DirectS)
        
        if len(P_DirectS)==0:
            P_Direct=[]
        else:
            
            P_Direct = [x/ Scaling for x in P_DirectS]
            
        if len(Q_DirectS)==0:
            Q_Direct=[]
        else:
     
            Q_Direct = [x/ Scaling for x in Q_DirectS]
            
        Direct_Control=[P_Direct,Q_Direct]
    	#time response for P
        return Direct_Control
#    
#    def volt_var(self, ts=datetime.utcnow(),location=0):
#        """
#        This function takes the date, time, and location of the BESS
#        and returns a reactive power set point according to the configured VV11 function
#        :param ts:datetime opject, location: numerical designation for the location of the BESS
#        :return q_req: reactive power set point based on FW21 function
#        '''"""
#        v = self.grid.get_voltage(ts,location)
#        
#        n = len(self.Vset)
#        q_req = self.Qset[0]
#        for i in range(n-1):
#            if v>self.Vset[i] and v<self.Vset[i+1] :
#                m =  (self.Qset[i] - self.Qset[i+1]) / (self.Vset[i] - self.Vset[i+1]) 
#                q_req = self.Qset[i] + m * (v - self.Vset[i])
#        return q_req
        
    def frequency_watt(self, ts=datetime.utcnow(),location=0):
        """
        This function takes the requested power, date, time, and location
        and modifys the requested power according to the configured FW21 
        :param p_req: real power requested, ts:datetime opject,
               location: numerical designation for the location of the BESS
        :return p_mod: modifyed real power based on FW21 function
        """
        f = self.grid.get_frequency(ts,location) 
        
        
        File_Path_Forecast=os.getcwd()+'\Forecast.npy'
        File_Path_OperatingPoint=os.getcwd()+'\Operating_Point_Pre.npy'
        [Time_,Pmpp_AC,Q_max_available_Plus,Q_max_available_Minus,eff_mpp]=np.load(File_Path_Forecast)
    
        [P_pre,Q_Pre,P_Requested,Q_Requested,Last_Time]=np.load(File_Path_OperatingPoint)
        ts_local=self.datetime_from_utc_to_local(ts)
        T_Stamp=[ts_local.year,ts_local.month,ts_local.day,ts_local.hour,ts_local.minute,ts.second]
 
        Current_Forecast_indx=self.Match_Time(Time_,T_Stamp)
        P_avl=Pmpp_AC[Current_Forecast_indx]/self.s_max
        P_min=self.p_min/self.s_max
        P_pre=P_pre/self.s_max
 
    
        if f<60-self.db_UF:
            P=min(P_pre+((60-self.db_UF)-f)/(60*self.k_UF),P_avl)
        elif f>60+self.db_OF:
            P=max(P_pre-(f-(60+self.db_OF))/(60*self.k_OF),P_min)
        else:
            """
            select the operating mode withing deadband range
            """
            P=P_avl
            
        dt = timedelta(hours=1)
        p_req = P*self.SubFleet_NumberOfUnits*self.s_max
        q_req = None
        # call run function with proper inputs
        
        
   
        fleet_response = self.Run_Fleet(ts=ts,sim_step=dt,P_req=p_req, Q_req=q_req, return_forecast=False,WP=self.is_P_priority)
#        print('t = ',ts_local,' f =',f, ' and p = ',P, 'P_avl = ',P_avl, 'P_pre = ',P_pre,' Current_Forecast_indx = ',Current_Forecast_indx)
        return fleet_response


    def Volt_Var(self, ts=datetime.utcnow(),location=0):
        """
        This function takes the requested power, date, time, and location
        and modifys the requested power according to the configured FW21 
        :param p_req: real power requested, ts:datetime opject,
               location: numerical designation for the location of the BESS
        :return p_mod: modifyed real power based on FW21 function
        """
        v = self.grid.get_voltage(ts,location) 
        
        V1=(1-self.delv1)*self.Vnom
        V2=(1-self.delv2)*self.Vnom
        V3=(1+self.delv3)*self.Vnom
        V4=(1+self.delv4)*self.Vnom
        
        Q1=self.Q1*self.SubFleet_NumberOfUnits*self.s_max
        Q2=self.Q2*self.SubFleet_NumberOfUnits*self.s_max
        Q3=self.Q3*self.SubFleet_NumberOfUnits*self.s_max
        Q4=-1*self.Q4*self.SubFleet_NumberOfUnits*self.s_max
        
        
        if v>=V2 and v<=V3:
            Q=Q2
        elif v>=V1 and v<V2:
            Q=(V2-v)*Q1/(V2-V1)
        elif v<V1:
            Q=Q1
        elif v>V3 and v<=V4:
            Q=-1*(V3-v)*Q4/(V3-V4)
        else:
            Q=-1*Q4
        
        dt = timedelta(hours=1)
        p_req = None
        q_req = Q
        # call run function with proper inputs
        
        
   
        fleet_response = self.Run_Fleet(ts=ts,sim_step=dt,P_req=p_req, Q_req=q_req, return_forecast=False,WP=self.is_P_priority)
#        print('t = ',ts_local,' f =',f, ' and p = ',P, 'P_avl = ',P_avl, 'P_pre = ',P_pre,' Current_Forecast_indx = ',Current_Forecast_indx)
        return fleet_response
    
#        
#        
        