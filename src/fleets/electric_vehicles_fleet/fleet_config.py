# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 10:11:45 2018

@author: rmahmud
"""


# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}


class FleetConfig:
    """
    This class describes configurable parameters of a fleet
    """

    def __init__(self, is_P_priority=True, is_autonomous=False, FW_Param=[], v_thresholds=[]):
        self.is_P_priority = is_P_priority
        self.is_autonomous = is_autonomous
        self.FW_Param = FW_Param # FW_Param=[db_UF,db_OF,k_UF,k_OF]
        self.v_thresholds = v_thresholds