# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 14:09:49 2018

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""

class BEM_Param(object):
    """creates Battrey equivalent model API for the interface between device
    to fleet and fleet to system operator"""
    def __init__(self,Name,NumberOfUnits=None,InverterModel=None,PanelModel=None,
                 NP_P_Max=None,NP_P_Min=None,NP_Q_plus=None,NP_Q_Minus=None,
                 NP_P_Ramp_UP=None,NP_P_Ramp_Down=None,NP_Q_Ramp_UP=None,
                 NP_Q_Ramp_Down=None,P_Max=None,P_Min=None,Q_Max=None,Q_Min=None,
                 P_Ramp_UP=None,P_Ramp_Down=None,Q_Ramp_UP=None,Q_Ramp_Down=None,
                 P_Output=None,Q_Output=None,P_Grid=None,Q_Grid=None,
                 P_GridBase=None,Q_GridBase=None,P_Service=None,Q_Service=None,
                 P_Load=None,P_LoadBase=None,t_hold=None,t_restore=None,SP=None,
                 Price_Elasticity=None,P_Requested=None, \
                 Q_Requested=None,Time_Steps=None):
#%% Nameplate parameters        
            self.Name=Name #unique identifier
            self.NumberOfUnits=NumberOfUnits # Total number of units in a group, i.e. fleet, subfleet
            self.InverterModel=InverterModel # self explained
            self.PanelModel=PanelModel # PV panel model
            self.NP_P_Max=NP_P_Max #Maximum real power for services
            self.NP_P_Min=NP_P_Min#Minimum real power for services
            self.NP_Q_Max_plus=NP_Q_plus#Maximum reactive power for services 
            self.NP_Q_Max_Minus=NP_Q_Minus#Minimum reactive power for services 
            self.NP_P_Ramp_UP=NP_P_Ramp_UP#Ramp rate real power up
            self.NP_P_Ramp_Down=NP_P_Ramp_Down#Ramp rate real power down
            self.NP_Q_Ramp_UP=NP_Q_Ramp_UP#Ramp rate reactive power up
            self.NP_Q_Ramp_Down=NP_Q_Ramp_Down#Ramp rate reactive power down
            
            
            
#%%Variables
            
            self.P_Max=P_Max#Maximum real power for services
            self.P_Min=P_Min##Minimum real power for services
            self.Q_Max=Q_Max#Maximum reactive power for services 
            self.Q_Min=Q_Min#Minimum real power for services
            self.P_Ramp_UP=P_Ramp_UP#Ramp rate real power up
            self.P_Ramp_Down=P_Ramp_Down#Ramp rate real power down
            self.Q_Ramp_UP=Q_Ramp_UP#Ramp rate reactive power up
            self.Q_Ramp_Down=Q_Ramp_Down#Ramp rate reactive power down
            self.P_Output=P_Output#Power output from generator, real
            self.Q_Output=Q_Output#Power output from generator, reactive 
            self.P_Grid=P_Grid#Power injected into grid, real
            self.Q_Grid=Q_Grid#Power injected into grid, reactive
            self.P_GridBase=P_GridBase#Power injected into grid, real, (base case) 
            self.Q_GridBase=Q_GridBase#Power injected into grid, reactive, (base case)
            self.P_Service=P_Service#Power delivered for service, real
            self.Q_Service=Q_Service#Power delivered for service, reactive
            self.P_Load=P_Load#Load
            self.P_LoadBase=P_LoadBase#Base load 
            self.P_Requested=P_Requested
            self.Q_Requested=Q_Requested
            self.Time_Steps=Time_Steps
            
#%%Behavioral Parameters
            self.t_hold=t_hold#Time limit, hold
            self.t_restore=t_restore#Time, restoration 
            self.SP=SP#Strike price 
            self.Price_Elasticity=Price_Elasticity#Price elasticity
            
#%% Addtional features of BEM API
        
    
    def add_NumberOfUnits(self,NumberOfUnits):
            self.NumberOfUnits=NumberOfUnits
            
    def add_InverterModel(self,InverterModel):
            self.InverterModel=InverterModel
            
    def add_PanelModel(self,PanelModel):
            self.PanelModel=PanelModel
            
    def add_NP_P_Max(self,NP_P_Max):
            self.NP_P_Max=NP_P_Max    
    def add_NP_P_Min(self,NP_P_Min):
            self.NP_P_Min=NP_P_Min
            
    def add_NP_Q_Minus(self,NP_Q_Minus):
            self.NP_Q_Minus=NP_Q_Minus
            
    def add_NP_Q_plus(self,NP_Q_plus):
            self.NP_Q_plus=NP_Q_plus
            
  #  def add_NP_Q_Min(self,NP_Q_Min):
    #        self.NP_Q_Min=NP_Q_Min
            
    def add_NP_P_Ramp_UP(self,NP_P_Ramp_UP):
            self.NP_P_Ramp_UP=NP_P_Ramp_UP
            
    def add_NP_P_Ramp_Down(self,NP_P_Ramp_Down):
            self.NP_P_Ramp_Down=NP_P_Ramp_Down
            
    def add_NP_Q_Ramp_UP(self,NP_Q_Ramp_UP):
            self.NP_Q_Ramp_UP=NP_Q_Ramp_UP
            
    def add_NP_Q_Ramp_Down(self,NP_Q_Ramp_Down):
            self.NP_Q_Ramp_Down=NP_Q_Ramp_Down
            
    def add_P_Max(self,P_Max):
            self.P_Max=P_Max
            
    def add_P_Min(self,P_Min):
            self.P_Min=P_Min
            
    def add_Q_Max(self,Q_Max):
            self.Q_Max=Q_Max
            
    def add_Q_Min(self,Q_Min):
            self.Q_Min=Q_Min
            
    def add_P_Ramp_UP(self,P_Ramp_UP):
            self.P_Ramp_UP=P_Ramp_UP
            
    def add_P_Ramp_Down(self,P_Ramp_Down):
            self.P_Ramp_Down=P_Ramp_Down
            
    def add_Q_Ramp_UP(self,Q_Ramp_UP):
            self.Q_Ramp_UP=Q_Ramp_UP
            
    def add_Q_Ramp_Down(self,Q_Ramp_Down):
            self.Q_Ramp_Down=Q_Ramp_Down
            
    def add_P_Output(self,P_Output):
            self.P_Output=P_Output
            
    def add_Q_Output(self,Q_Output):
            self.Q_Output=Q_Output
            
    def add_P_Grid(self,P_Grid):
            self.P_Grid=P_Grid
            
    def add_Q_Grid(self,Q_Grid):
            self.Q_Grid=Q_Grid
            
    def add_P_GridBase(self,P_GridBase):
            self.P_GridBase=P_GridBase
            
    def add_Q_GridBase(self,Q_GridBase):
            self.Q_GridBase=Q_GridBase
            
    def add_P_Service(self,P_Service):
            self.P_Service=P_Service
            
    def add_Q_Service(self,Q_Service):
            self.Q_Service=Q_Service
            
    def add_P_Load(self,P_Load):
            self.P_Load=P_Load
            
    def add_P_LoadBase(self,P_LoadBase):
            self.P_LoadBase=P_LoadBase
    
    
