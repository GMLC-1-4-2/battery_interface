# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 13:41:32 2018

@author: rmahmud
# Software record # SWR-18-22
# National Renewable Energy Laboratory, Golden, CO, USA
"""
def data_M2453BB():
	#Information from the solar array datasheet

	Iscn = 8.89            #%Nominal short-circuit voltage [A] 
	Vocn = 37.8            #%Nominal array open-circuit voltage [V] 
	Imp = 8.18             #%Array current @ maximum power point [A] 
	Vmp = 31.2             #%Array voltage @ maximum power point [V] 
	Pmax_e = Vmp*Imp       #%Array maximum output peak power [W] 
	Kv = -0.35/100*Vocn            #%Voltage/temperature coefficient [V/K] 
	Ki = 0.056/100*Iscn           #%Current/temperature coefficient [A/K] 
	Ns = 60                #%Nunber of series cells 
	return Iscn,Vocn , Imp ,Vmp , Pmax_e ,Kv , Ki ,Ns 
