# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 14:40:48 2018

@author: rmahmud
"""

# -*- coding: utf-8 -*-
def Fleet(ts,sim_step,P_req, Q_req, return_forecast): 
 # this module aggregates the PV information from a large pool of PV/invertre system
# Updates prepares report for system operator based on PV fleet
# Breaks down the operation command from system operator to subfleet and device level   
    
    import Weather
    import Devices_
    import BEq_PV
    import PV_Inverter_Data
    import Aggregator_Command
    
    
    

    
    def Grid_Param():
        from grid_info import GridInfo
        a=GridInfo()
        V=a.get_voltage('XX')
        f=a.get_frequency('XX')
        return f, V
        
 
    
    
    
# pull information about the PV subfleet

    #P_rated
    [Efficiency,Vdc,DC_Power,Rating,F_P,F_Q,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
    [P_rated,P_min,S_max,Qmax_Plus,Qmax_minus]=Rating
    [P_up,P_down,Q_up,Q_down]=Ramp_Limit
    

   
# Create Battery equivalent model (BEM) variables for the subfleets and PV fleet    
    SubFleetA=BEq_PV
    Fleet_PV=BEq_PV
    
   
    SubFleetA.Name='A'
    SubFleetA.NumberOfUnits=1e3
    SubFleetA.InverterModel='data_M2453BB'
    SubFleetA.PanelModel='ABB_MICRO_025'
    SubFleetA.NP_C=[]           
    SubFleetA.NP_P_grid_max=P_rated*SubFleetA.NumberOfUnits#Minimum real power for services
    SubFleetA.NP_Q_grid_max=Qmax_Plus*SubFleetA.NumberOfUnits#Maximum reactive power for services 
    SubFleetA.NP_P_grid_min=P_min*SubFleetA.NumberOfUnits#Minimum reactive power for services 
    SubFleetA.NP_Q_grid_min=Qmax_minus*SubFleetA.NumberOfUnits#Ramp rate real power up
    SubFleetA.NP_P_service_max=SubFleetA.NP_P_grid_max-SubFleetA.NP_P_grid_min#Ramp rate real power down
    SubFleetA.NP_Q_service_max=SubFleetA.NP_Q_grid_max-SubFleetA.NP_Q_grid_min#Ramp rate reactive power up
    SubFleetA.NP_P_service_min=0#Ramp rate reactive power down
    SubFleetA.NP_Q_service_min=0
    SubFleetA.NP_P_up=P_up
    SubFleetA.NP_Q_up=Q_up
    SubFleetA.NP_P_down=P_down
    SubFleetA.NP_Q_down=Q_down
    SubFleetA.NP_e_in=[]
    SubFleetA.NP_e_out=[]
    

    Fleet_PV.Name='PV'
    Fleet_PV.NumberOfUnits=SubFleetA.NumberOfUnits
    Fleet_PV.InverterModel=[]
    Fleet_PV.PanelModel=[]
    Fleet_PV.NP_C=[]           
    Fleet_PV.NP_P_grid_max=SubFleetA.NP_P_grid_max#Minimum real power for services
    Fleet_PV.NP_Q_grid_max=SubFleetA.NP_Q_grid_max#Maximum reactive power for services 
    Fleet_PV.NP_P_grid_min=SubFleetA.NP_P_grid_min#Minimum reactive power for services 
    Fleet_PV.NP_Q_grid_min=SubFleetA.NP_Q_grid_min#Ramp rate real power up
    Fleet_PV.NP_P_service_max=SubFleetA.NP_P_service_max#Ramp rate real power down
    Fleet_PV.NP_Q_service_max=SubFleetA.NP_Q_service_max#Ramp rate reactive power up
    Fleet_PV.NP_P_service_min=0#Ramp rate reactive power down
    Fleet_PV.NP_Q_service_min=0
    Fleet_PV.NP_P_up=SubFleetA.NP_P_up
    Fleet_PV.NP_Q_up=SubFleetA.NP_Q_up
    Fleet_PV.NP_P_down=SubFleetA.NP_P_down
    Fleet_PV.NP_Q_down=SubFleetA.NP_Q_down
    Fleet_PV.NP_e_in=[]
    Fleet_PV.NP_e_out=[]
    

    
    

    #Calculate Nameplate information on subfleet

    
    
    #Calculate Nameplate information on Fleet

    
    #self,Name,NumberOfUnits=None,InverterModel=None,PanelModel=None,
     #       NP_P_Max=None,NP_P_Min=None,NP_Q_Max=None,NP_Q_Min=None,
      #      NP_P_Ramp_UP=None,NP_P_Ramp_Down=None,NP_Q_Ramp_UP=None,
       #     NP_Q_Ramp_Down=None,P_Max=None,P_Min=None,Q_Max=None,Q_Min=None,
        #             P_Ramp_UP=None,P_Ramp_Down=None,Q_Ramp_UP=None,Q_Ramp_Down=None,
         #            P_Output=None,Q_Output=None,P_Grid=None,Q_Grid=None,
          #           P_GridBase=None,Q_GridBase=None,P_Service=None,Q_Service=None,
    
        
   # break down the command for fleet to command for device  
    Command_to_Device=Aggregator_Command.Aggregator_Command(P_req, Q_req, \
                                                            SubFleetA.NumberOfUnits)
    
 
         
            
        # Grid parameters required for autonomous mode of operation
       
        
        #[Time_,P_rec,Q_rec,P_req_,Q_req_,P_MPP,G_rec,T_rec]\
    [P_grid,Q_grid,P_service,Q_service,E_t0,c,P_output,Q_output,P_grid_max,Q_grid_max,\
         P_grid_min,Q_grid_min,P_service_max,Q_service_max,P_service_min,Q_service_min,del_t_hold,\
         t_restore,SP,N_req,Effeciency]=Devices_.Device_PV(ts,sim_step,Weather,Grid_Param,Command_to_Device,return_forecast)
                  
        #print(P_Output)    
    SubFleetA.P_grid=P_grid* SubFleetA.NumberOfUnits
    SubFleetA.Q_grid=Q_grid* SubFleetA.NumberOfUnits
    SubFleetA.P_service=P_service* SubFleetA.NumberOfUnits
    SubFleetA.Q_service=Q_service* SubFleetA.NumberOfUnits
    SubFleetA.E_t0=E_t0
    SubFleetA.c=c
    
    SubFleetA.P_output=[x*SubFleetA.NumberOfUnits for x in P_output]
    SubFleetA.Q_output=[x*SubFleetA.NumberOfUnits for x in Q_output]
    SubFleetA.P_grid_max=[x*SubFleetA.NumberOfUnits for x in P_grid_max]
    SubFleetA.Q_grid_max=[x*SubFleetA.NumberOfUnits for x in Q_grid_max]
    SubFleetA.P_grid_min=[x*SubFleetA.NumberOfUnits for x in P_grid_min]
    SubFleetA.Q_grid_min=[x*SubFleetA.NumberOfUnits for x in Q_grid_min]
    SubFleetA.P_service_max=[x*SubFleetA.NumberOfUnits for x in P_service_max]
    SubFleetA.Q_service_max=[x*SubFleetA.NumberOfUnits for x in Q_service_max]
    SubFleetA.P_service_min=[x*SubFleetA.NumberOfUnits for x in P_service_min]
    SubFleetA.Q_service_min=[x*SubFleetA.NumberOfUnits for x in Q_service_min]
    SubFleetA.del_t_hold=del_t_hold
    SubFleetA.t_restore=t_restore
    SubFleetA.SP=SP
    SubFleetA.N_req=N_req
    SubFleetA.NP_e_out=Effeciency
    
    # Calculate information about Subfleets    
    
    # Calculate information about Device Fleet: PV
    # Calculate information about Subfleets    
    Fleet_PV.P_grid=SubFleetA.P_grid
    Fleet_PV.Q_grid=SubFleetA.Q_grid
    Fleet_PV.P_service=SubFleetA.P_service
    Fleet_PV.Q_service=SubFleetA.Q_service
    Fleet_PV.E_t0=SubFleetA.E_t0
    Fleet_PV.c=SubFleetA.c
    
    Fleet_PV.P_output=SubFleetA.P_output
    Fleet_PV.Q_output=SubFleetA.Q_output
    Fleet_PV.P_grid_max=SubFleetA.P_grid_max
    Fleet_PV.Q_grid_max=SubFleetA.Q_grid_max
    Fleet_PV.P_grid_min=SubFleetA.P_grid_min
    Fleet_PV.Q_grid_min=SubFleetA.Q_grid_min
    Fleet_PV.P_service_max=SubFleetA.P_service_max
    Fleet_PV.Q_service_max=SubFleetA.Q_service_max
    Fleet_PV.P_service_min=SubFleetA.P_service_min
    Fleet_PV.Q_service_min=SubFleetA.Q_service_min
    Fleet_PV.del_t_hold=SubFleetA.del_t_hold
    Fleet_PV.t_restore=SubFleetA.t_restore
    Fleet_PV.SP=SubFleetA.SP
    Fleet_PV.N_req=SubFleetA.N_req
    
    return Fleet_PV
 
        


#Fleet_P_Max=