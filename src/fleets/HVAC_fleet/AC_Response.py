# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 2018
For GMLC 1.4.2, 
Creating the Fleet Interface

@author: Jin Dong (ORNL), Teja Kuruganti (ORNL)
"""

from datetime import datetime


class ACResponse:
    """
    This class describes 1-timestep output of a HVAC
    """

    def __init__(self, ts=datetime.utcnow()):
        """
        Constructor with default values
        """
        
        self.TinB = 0
        self.TwallB = 0
        self.TmassB = 0
        self.TatticB = 0
        self.SOC_b = 0
        self.ElementOnB = 0

        self.Tin = 0
        self.Twall = 0
        self.Tmass = 0
        self.Tattic = 0


        self.Tset = 0 
        self.Eused = 0 
        self.Pbase = 0

        self.lockoffB = 0
        self.lockonB = 0 
        self.lockoff = 0
        self.lockon = 0
        self.sim_step = 0

        self.cycle_off_grid = 0
        self.cycle_on_grid = 0

        self.cycle_off_base = 0
        self.cycle_on_base = 0

        self.PusedMax = 0
        self.PusedMin = 0
        self.ElementOn = 0
        self.Eservice = 0
        self.SOC = 0
        self.AvailableCapacityAdd = 0
        self.AvailableCapacityShed = 0
        self.ServiceCallsAccepted = 0
        self.IsAvailableAdd = 0
        self.IsAvailableShed = 0
        
#        return tin, twall, tmass, tattic, tset, eused, pusedmax, eloss, elementon, eservice, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, isAvailableAdd, isAvailableShed
