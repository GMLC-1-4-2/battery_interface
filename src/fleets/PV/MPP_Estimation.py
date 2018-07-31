# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 11:17:54 2017

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""

def MPP_Estimation(G,T):
    
    import PV
    import PV_Inverter_Data
    import numpy
    from scipy.interpolate import interp1d
    
    
    [ Pmpp,Vmpp]=PV.PV(G,T)
    
    
    [Efficiency,Vdc,DC_Power,Rating,F_P,F_Q,Ramp_Limit]=PV_Inverter_Data.ABB_MICRO_025()
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
    
            