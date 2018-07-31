# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 14:47:15 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def Limit_Check(P_rated,Pmpp_AC,S_max,P,Q,WP):
    import numpy as np
    
    if P>np.minimum(P_rated,Pmpp_AC):
        P=np.minimum(P_rated,Pmpp_AC)
    
    S=np.sqrt(np.power(P,2)+np.power(Q,2));
    if S>S_max:
        if WP==1:#%watt priority
            Q=np.sqrt(np.power(S_max,2)-np.power(P,2))
        else:# % var priority
            P=np.sqrt(np.power(S_max,2)-np.power(Q,2))
            

    return P,Q            
               