# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 13:41:32 2018

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def Fleet(SystemOperatorCommand): 
 # this module aggregates the PV information from a large pool of PV/invertre system
# Updates prepares report for system operator based on PV fleet
# Breaks down the operation command from system operator to subfleet and device level   
    import Aggregator_Command
    import Weather
    import Devices
    from BEM import BEM_Param
    import PV_Inverter_Data
    
    
    
    import SystemOperatorCommand
    Request='Forecast'
    
    def Grid_Param():
            f = 60.1
            V = 1.1
            return f, V
        
 
    
    
    
# pull information about the PV subfleet
    [Efficiency,Vdc,DC_Power,Rating,F_P,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
    [P_rated,P_min,S_max,Qmax_Plus,Qmax_minus]=Rating
    

   
# Create Battery equivalent model (BEM) variables for the subfleets and PV fleet    
    SubFleetA=BEM_Param('A')
    Fleet_PV=BEM_Param('PV')
    
    
    SubFleetA.add_NumberOfUnits(1e3)
    SubFleetA.add_PanelModel('data_M2453BB')
    SubFleetA.add_InverterModel('ABB_MICRO_025')
    
    #Calculate Nameplate information on subfleet
    SubFleetA.NP_P_Max=(P_rated*SubFleetA.NumberOfUnits)
    SubFleetA.NP_P_Min=(P_min*SubFleetA.NumberOfUnits)
    SubFleetA.NP_Q_plus=(Qmax_Plus*SubFleetA.NumberOfUnits)
    SubFleetA.NP_Q_Minus=(Qmax_minus*SubFleetA.NumberOfUnits)
    
    
    #Calculate Nameplate information on Fleet
    Fleet_PV.NP_P_Max=(SubFleetA.NP_P_Max)
    Fleet_PV.NP_P_Min=(SubFleetA.NP_P_Min)
    Fleet_PV.NP_Q_plus=(SubFleetA.NP_Q_plus)
    Fleet_PV.NP_Q_Minus=(SubFleetA.NP_Q_Minus)
    
    #self,Name,NumberOfUnits=None,InverterModel=None,PanelModel=None,
     #       NP_P_Max=None,NP_P_Min=None,NP_Q_Max=None,NP_Q_Min=None,
      #      NP_P_Ramp_UP=None,NP_P_Ramp_Down=None,NP_Q_Ramp_UP=None,
       #     NP_Q_Ramp_Down=None,P_Max=None,P_Min=None,Q_Max=None,Q_Min=None,
        #             P_Ramp_UP=None,P_Ramp_Down=None,Q_Ramp_UP=None,Q_Ramp_Down=None,
         #            P_Output=None,Q_Output=None,P_Grid=None,Q_Grid=None,
          #           P_GridBase=None,Q_GridBase=None,P_Service=None,Q_Service=None,
    
        
   # break down the command for fleet to command for device  
    Command_to_Device=Aggregator_Command.Aggregator_Command( \
        SystemOperatorCommand,SubFleetA.NumberOfUnits)
    Request=Command_to_Device[0]
    if Request!='Forecast':   
         
            
        # Grid parameters required for autonomous mode of operation
       
        
        #[Time_,P_rec,Q_rec,P_req_,Q_req_,P_MPP,G_rec,T_rec]\
        
        [P_Max,P_Min,Q_Max_Plus,Q_Max_Minus, \
        P_Ramp_UP,P_Ramp_Down,Q_Ramp_UP,Q_Ramp_Down,P_Load, \
        P_Output,Q_Output,P_GridBase,Q_GridBase,P_Grid,Q_Grid, \
        P_Requested,Q_Requested,Time_] = \
        Devices.Device_PV(Weather,Grid_Param,Command_to_Device)
            
          
        #print(P_Output)    
        # Calculate information about Subfleets    
        SubFleetA.P_Max=P_Max* SubFleetA.NumberOfUnits
        SubFleetA.P_Min=P_Min* SubFleetA.NumberOfUnits
        SubFleetA.Q_Max_Plus=Q_Max_Plus* SubFleetA.NumberOfUnits
        SubFleetA.Q_Max_Minus=Q_Max_Minus* SubFleetA.NumberOfUnits
        SubFleetA.P_Ramp_UP=P_Ramp_UP* SubFleetA.NumberOfUnits
        SubFleetA.P_Ramp_Down=P_Ramp_Down* SubFleetA.NumberOfUnits
        SubFleetA.Q_Ramp_UP=Q_Ramp_UP* SubFleetA.NumberOfUnits
        SubFleetA.P_Load=P_Load* SubFleetA.NumberOfUnits
        SubFleetA.P_Output=[x* SubFleetA.NumberOfUnits for x in P_Output]
        SubFleetA.Q_Output=Q_Output* SubFleetA.NumberOfUnits
        SubFleetA.P_GridBase=P_GridBase* SubFleetA.NumberOfUnits
        SubFleetA.Q_GridBase=[x * SubFleetA.NumberOfUnits for x in Q_GridBase]
        SubFleetA.P_Grid=[x* SubFleetA.NumberOfUnits for x in P_Grid]
        SubFleetA.Q_Grid=Q_Grid* SubFleetA.NumberOfUnits
        SubFleetA.P_Requested=P_Requested* SubFleetA.NumberOfUnits
        SubFleetA.Q_Requested=Q_Requested* SubFleetA.NumberOfUnits
        SubFleetA.Time_Steps=Time_
        
        # Calculate information about Device Fleet: PV
        # Calculate information about Subfleets    
        Fleet_PV.P_Max=SubFleetA.P_Max
        Fleet_PV.P_Min=SubFleetA.P_Min
        Fleet_PV.Q_Max_Plus=SubFleetA.Q_Max_Plus
        Fleet_PV.Q_Max_Minus=SubFleetA.Q_Max_Minus
        Fleet_PV.P_Ramp_UP=SubFleetA.P_Ramp_UP
        Fleet_PV.P_Ramp_Down=SubFleetA.P_Ramp_Down
        Fleet_PV.Q_Ramp_UP=SubFleetA.Q_Ramp_UP
        Fleet_PV.P_Load=SubFleetA.P_Load
        Fleet_PV.P_Output=SubFleetA.P_Output
        Fleet_PV.Q_Output=SubFleetA.Q_Output
        Fleet_PV.P_GridBase=SubFleetA.P_GridBase
        Fleet_PV.Q_GridBase=SubFleetA.Q_GridBase
        Fleet_PV.P_Grid=SubFleetA.P_Grid
        Fleet_PV.Q_Grid=SubFleetA.Q_Grid
        Fleet_PV.P_Requested=SubFleetA.P_Requested
        Fleet_PV.Q_Requested=SubFleetA.Q_Requested
        Fleet_PV.Time_Steps=SubFleetA.Time_Steps
      
        return Fleet_PV
    else:
        [Time_,Pmpp_AC,Q_Max_Plus,Q_Max_Minus]= \
         Devices.Device_PV(Weather,Grid_Param,Command_to_Device)
        
        P_Min=0
        SubFleetA.P_Max=[x * SubFleetA.NumberOfUnits for x in Pmpp_AC]
        SubFleetA.P_Min= P_Min*0
        SubFleetA.Q_Max_Plus=[x * SubFleetA.NumberOfUnits for x in Q_Max_Plus]
        SubFleetA.Q_Max_Minus=[x * SubFleetA.NumberOfUnits for x in Q_Max_Minus]
        SubFleetA.Time_Steps=Time_
       
        Fleet_PV.P_Max=SubFleetA.P_Max
        Fleet_PV.P_Min=SubFleetA.P_Min
        Fleet_PV.Q_Max_Plus=SubFleetA.Q_Max_Plus
        Fleet_PV.Q_Max_Minus=SubFleetA.Q_Max_Minus
        Fleet_PV.Time_Steps=SubFleetA.Time_Steps
        
       
        
        #print(Fleet_PV.Time_Steps)
        return Fleet_PV
         
        
         
         
        
        


#Fleet_P_Max=