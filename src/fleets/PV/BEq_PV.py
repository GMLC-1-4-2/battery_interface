# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 13:45:21 2018

@author: rmahmud
"""

class BEq_PV(object):
    """Class for a fleet of PVs"""
    def _init_(self,Name,NumberOfUnits,InverterModel,PanelModel,NP_C,NP_P_grid_max,
               NP_Q_grid_max,NP_P_grid_min,NP_Q_grid_min,NP_P_service_max,NP_Q_service_max,
               NP_P_service_min,NP_Q_service_min,NP_P_up,NP_Q_up,NP_P_down,NP_Q_down,NP_e_in,
               NP_e_out):
        #%% Nameplate parameters        
        self.Name=Name #unique identifier
        self.NumberOfUnits=NumberOfUnits # Total number of units in a group, i.e. fleet, subfleet
        self.InverterModel=InverterModel # self explained
        self.PanelModel=PanelModel # PV panel model
        self.NP_C=NP_C #Maximum real power for services
        self.NP_P_grid_max=NP_P_grid_max#Minimum real power for services
        self.NP_Q_grid_max=NP_Q_grid_max#Maximum reactive power for services 
        self.NP_P_grid_min=NP_P_grid_min#Minimum reactive power for services 
        self.NP_Q_grid_min=NP_Q_grid_min#Ramp rate real power up
        self.NP_P_service_max=NP_P_service_max#Ramp rate real power down
        self.NP_Q_service_max=NP_Q_service_max#Ramp rate reactive power up
        self.NP_P_service_min=NP_P_service_min#Ramp rate reactive power down
        self.NP_Q_service_min=NP_Q_service_min
        self.NP_P_up=NP_P_up
        self.NP_Q_up=NP_Q_up
        self.NP_P_down=NP_P_down
        self.NP_Q_down=NP_Q_down
        self.NP_e_in=NP_e_in
        self.NP_e_out=NP_e_out
        
    def update_state(self,P_grid,Q_grid,P_service,Q_service,E_t0,c,P_output,Q_output,
                     P_grid_max,Q_grid_max,P_grid_min,Q_grid_min,P_service_max,Q_service_max,
                     P_service_min,Q_service_min,t_restore,SP,N_req,del_t_hold):
        

        self.P_grid=P_grid
        self.Q_grid=Q_grid
        self.P_service=P_service
        self.Q_service=Q_service
        self.E_t0=E_t0
        self.c=c
        self.P_output=P_output
        self.Q_output=Q_output
        self.P_grid_max=P_grid_max
        self.Q_grid_max=Q_grid_max
        self.P_grid_min=P_grid_min
        self.Q_grid_min=Q_grid_min
        self.P_service_max=P_service_max
        self.Q_service_max=Q_service_max
        self.P_service_min=P_service_min
        self.Q_service_min=Q_service_min
        self.del_t_hold=del_t_hold
        self.t_restore=t_restore
        self.SP=SP
        self.N_req=N_req
        
        
                             
    def service_response(P_req=None, Q_req=None, return_forecast=False):
        import Fleet_PV
        Fleet_PV=Fleet_PV.Fleet(P_req, Q_req, return_forecast)
              
        return Fleet_PV
  
    