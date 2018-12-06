# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 10:17:07 2018

@author: rmahmud
"""

class FrequencyDroop(object):
    """
    This class describes Frequency-Droop operation of device fleet
    """
    def __init__(self,db_UF,db_OF,k_UF,k_OF,P_avl,P_min,P_pre):

        """
        initiating variables to evaluate the Frequency-Droop function
        parameters defining curve: db_UF,db_OF,k_UF,k_OF
        State variable: P_avl,P_min,P_pre
        
        State variables will be updated by the fleet whenever the state of the fleet changes
        parameters will be updated by the high level controller whenever a new frequency-droop curve is required 
        """
        #self.Category=Category # DER category, e.g. I, II or III
        self.db_UF=db_UF#single-sided deadband value for low-frequency, in Hz
        self.db_OF=db_OF#single-sided deadband value for high-frequency, in Hz
        self.k_UF=k_UF#per-unit frequency change corresponding to 1 per-unit
#                       power output change (frequency droop), unitless
        self.k_OF=k_OF#per-unit frequency change corresponding to 1 per-unit
#                       power output change (frequency droop), unitless
        self.P_avl=P_avl#available active power, in p.u. of the DER rating
        self.P_min=P_min#minimum active power output due to DER prime mover 
        #               constraints, in p.u. of the DER rating
        self.P_pre=P_pre# pre-disturbance active power output, defined by the 
#        active power output at the point of time the frequency exceeds the 
#        deadband, in p.u. of the DER rating
        
    def F_W(self,f):
        """
        Implementing Frequency-Droop operation; Reference: Table 23, IEEE1547-2018
        """
        if f<60-self.db_UF:
            P=min(self.P_pre+((60-self.db_UF)-f)/(60*self.k_UF),self.P_avl)
        elif f>60+self.db_OF:
            P=max(self.P_pre-(f-(60+self.db_OF))/(60*self.k_OF),self.P_min)
        else:
            """
            select the operating mode withing deadband range
            """
            P=self.P_avl
        return P
                
        