# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 16:12:09 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""

def Aggregator_Command(P_DirectS, Q_DirectS,Scaling):
    
    # breaks down the command for aggregator to command for device

    import collections
    def get_iterable(x):
        if isinstance(x, collections.Iterable):
            return x
        else:
            return (x,)
    
    P_DirectS=get_iterable(P_DirectS)
    Q_DirectS=get_iterable(Q_DirectS)
    
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