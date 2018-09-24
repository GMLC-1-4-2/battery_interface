# -*- coding: utf-8 -*-
"""
Description: It contains the interface to interact with the fleet of electric 
vehicles: ElectricVehiclesFleet

Last update: 09/20/2018
Version: 1.0
Author: afernandezcanosa@anl.gov
"""

from fleet_interface import FleetInterface
from fleet_request   import FleetRequest
from fleet_response  import FleetResponse

import numpy as np
import pandas as pd
import os
from scipy.stats import truncnorm

class ElectricVehiclesFleet(FleetInterface):
    
    def __init__(self, ts):
        """
        Constructor
        """
        
        # Number of subfleets that are going to be simulated
        self.N_SubFleets = 100
        # Location of working path
        dirname = os.path.dirname(__file__)
        # Read the vehicle models and store them in a pandas dataframe
        self.df_VehicleModels = pd.read_csv(os.path.join(dirname,'data/vehicle_models.csv' ))  
        # Number of vehicle models
        self.N_Models = self.df_VehicleModels.shape[0]
        # Total number of vehicles
        self.N_Vehicles = self.df_VehicleModels['Total_Vehicles'].sum()
        # Number of subfleets of each vehicle model: e.g. 1st model = 50 sub fleets, 2nd model = 25 sub fleets, ...
        self.N_VehiclesSubFleet = []
        for v in range(self.N_Models):
            self.N_VehiclesSubFleet.append(int(self.N_SubFleets*(self.df_VehicleModels['Total_Vehicles'][v]/self.N_Vehicles)))
        # Vehicles per subfleef
        self.VehiclesSubFleet = int(self.N_Vehicles/self.N_SubFleets)    
        # Assign vehicles to the array of subfleets - variable used to perform logic operations
        NL = 0; NR = 0
        self.SubFleetId = np.zeros([self.N_SubFleets,], dtype = int)
        for i in range(self.N_Models):
            NR = NR + self.N_VehiclesSubFleet[i]
            self.SubFleetId[NL:NR] = i*np.ones(self.N_VehiclesSubFleet[i])
            NL = NL + self.N_VehiclesSubFleet[i]   
            
        # Weibull distribution: From statistical studies of the NHTS survey
        self.a = 3                                          # a value of the exponent
        peak = 1/3                                          # Peak in 1/3 of the range
        self.lambd = peak/(((self.a-1)/self.a)**(1/self.a)) # Shape value 
        
        # Read data from NHTS survey      
        self.df_Miles     = pd.read_table(os.path.join(dirname,'data/TRPMILES_filt.txt'), delim_whitespace=True, header=None)
        self.df_StartTime = pd.read_table(os.path.join(dirname,'data/STRTTIME_filt.txt'), delim_whitespace=True, header=None)
        self.df_EndTime   = pd.read_table(os.path.join(dirname,'data/ENDTIME_filt.txt') , delim_whitespace=True, header=None)
        self.df_WhyTo     = pd.read_table(os.path.join(dirname,'data/WHYTO_filt.txt' )  , delim_whitespace=True, header=None)
        
        # Percentage of cars that are charged at work/other places: Statistical studies from real data
        self.ChargedAtWork_per  = 0.17
        self.ChargedAtOther_per = 0.02

        # Initialize local time of the class
        self.initial_time = self.get_time_of_the_day(ts)
        self.time = self.get_time_of_the_day(ts)
        self.dt = 1
        
        # Mix of charging strategies: charging right away, start charging at midnight, start charging to be fully charged before the TCIN (percentage included)
        self.strategies = [ ['right away', 'midnight', 'tcin'], [0.4, 0.3, 0.3] ]
        # Charging strategy corresponding to each sub fleet
        self.monitor_strategy = []
        for i in range(len(self.strategies[0])):
            self.monitor_strategy = self.monitor_strategy + [self.strategies[0][i]]*int(self.strategies[1][i]*self.N_SubFleets)
        
        # Read the SOC curves from baseline Montecarlo simulations of the different charging strategies
        self.df_SOC_curves = pd.read_csv(os.path.join(dirname,'data/SOC_curves_charging_modes.csv' ))
        
        # Read the baseline power from Montecarlo simulations of the different charging strategies
        self.df_baseline_power = pd.read_csv(os.path.join(dirname,'data/power_baseline_charging_modes.csv' ))
        self.p_baseline = 0

        # Initial state of charge of all the subfleets => Depends on the baseline simulations (SOC curves)
        np.random.seed(0)
        self.SOC = np.zeros([self.N_SubFleets,]); i = 0
        for strategy in self.monitor_strategy:
            if strategy == 'right away':
                self.SOC[i] = truncnorm.rvs(((0 - self.df_SOC_curves['SOC_mean_RightAway'][self.initial_time])/self.df_SOC_curves['SOC_std_RightAway'][self.initial_time]), 
                                            ((1 - self.df_SOC_curves['SOC_mean_RightAway'][self.initial_time])/self.df_SOC_curves['SOC_std_RightAway'][self.initial_time]), 
                                            loc = self.df_SOC_curves['SOC_mean_RightAway'][self.initial_time], scale = self.df_SOC_curves['SOC_std_RightAway'][self.initial_time], size = 1)
            elif strategy == 'midnight':
                self.SOC[i] = truncnorm.rvs(((0 - self.df_SOC_curves['SOC_mean_Midnight'][self.initial_time])/self.df_SOC_curves['SOC_std_Midnight'][self.initial_time]), 
                                            ((1 - self.df_SOC_curves['SOC_mean_Midnight'][self.initial_time])/self.df_SOC_curves['SOC_std_Midnight'][self.initial_time]), 
                                            loc = self.df_SOC_curves['SOC_mean_Midnight'][self.initial_time], scale = self.df_SOC_curves['SOC_std_Midnight'][self.initial_time], size = 1)
            else:
                self.SOC[i] = truncnorm.rvs(((0 - self.df_SOC_curves['SOC_mean_TCIN'][self.initial_time])/self.df_SOC_curves['SOC_std_TCIN'][self.initial_time]), 
                                            ((1 - self.df_SOC_curves['SOC_mean_TCIN'][self.initial_time])/self.df_SOC_curves['SOC_std_TCIN'][self.initial_time]), 
                                            loc = self.df_SOC_curves['SOC_mean_TCIN'][self.initial_time], scale = self.df_SOC_curves['SOC_std_TCIN'][self.initial_time], size = 1)
            i += 1
            
        # Calculate the voltage to calculate the range in the function to match the schedule: It is conservative to say that V = V_OC 
        self.Voltage = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                            self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                            self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                            self.df_VehicleModels['Number_of_cells'][self.SubFleetId],self.SOC,0,0)
        
        # Schedules of all the sub fleets
        self.ScheduleStartTime, self.ScheduleEndTime, self.ScheduleMiles, self.SchedulePurpose, self.ScheduleTotalMiles = self.match_schedule(0,self.SOC,self.Voltage)
        
    def get_time_of_the_day(self, ts):
        """ Method to calculate the time of the day in seconds to for the discharge and charge of the subfleets """
        h, m, s = ts.hour, ts.minute, ts.second
        # Convert the hours, minutes, and seconds to seconds: referenced to 4 AM
        t = int(h) * 3600 + int(m) * 60 + int(s) - 4*3600
        if t >= 0:
            return t
        else:
            return t + 24*3600
    
    def process_request(self, fleet_request):
        """
        Request for timestep ts

        :param P_req:
        :param Q_req:

        :return res: an instance of FleetResponse
        """
        # call simulate method with proper inputs
        FleetResponse = self.simulate(fleet_request.P_req, fleet_request.Q_req, self.SOC, self.time, self.dt)

        return FleetResponse
    
    def simulate(self, P_req, Q_req, initSOC, t, dt):
        """ Simulation part of the code: discharge, charge, ... """

        self.p_baseline = (self.strategies[1][0]*self.df_baseline_power['power_RightAway_kW'].iloc[self.time] + 
                           self.strategies[1][1]*self.df_baseline_power['power_Midnight_kW'].iloc[self.time] + 
                           self.strategies[1][2]*self.df_baseline_power['power_TCIN_kW'].iloc[self.time])

        p_total = self.p_baseline + P_req

        if any(initSOC) > 1 or any(initSOC) < 0:
            print('ERROR: initial SOC out of range')
            return [[], []]
        else:
            response = FleetResponse()
            
            # SOC at the next time step
            SOC_step = np.zeros([self.N_SubFleets,])
            SOC_step[:] = initSOC[:]
            v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                        self.df_VehicleModels['Number_of_cells'][self.SubFleetId],initSOC,0,0)
            R = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId],
                                        self.df_VehicleModels['R_SOC_1'][self.SubFleetId],
                                        self.df_VehicleModels['R_SOC_2'][self.SubFleetId], initSOC)
            
            # power of demanded by each sub fleet
            power_subfleet = np.zeros([self.N_SubFleets,])
            for subfleet in range(self.N_SubFleets):
                
                # Discharge while driving
                if self.state_of_the_subfleet(t,subfleet) == 'driving':  
                    # Discharge rate for each sub fleet
                    discharge_rate = self.df_VehicleModels['Wh_mi'][self.SubFleetId[subfleet]]/(v_oc.iloc[subfleet]*self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet]])
                    trip_id  = self.trip_identification(t,subfleet)
                    avg_speed = self.average_speed_of_trip_miles_per_second(subfleet, trip_id)
                    SOC_step[subfleet] = initSOC[subfleet] - discharge_rate*avg_speed*dt
                    power_subfleet[subfleet] = 0
                                      
                # Certain amount of the vehicles of each sub fleet are charged at work: real data -> uncontrolled charging
                elif self.state_of_the_subfleet(t,subfleet) == 'work':
                    power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet]]
                    power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet]],
                                                     self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet]],
                                                     self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet]],
                                                     self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet]],power_ac)
                    ibat_charging = self.current_charging(v_oc.iloc[subfleet],R.iloc[subfleet],power_dc) 
                    Ah_rate = ibat_charging/3600
                    charge_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet]]
                    
                    # State of charge at the next time step and power of the subfleet
                    SOC_step[subfleet] = initSOC[subfleet] + charge_rate*self.ChargedAtWork_per*dt
                    power_subfleet[subfleet] = power_ac*self.ChargedAtWork_per*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet]])/1000
                    # Check if the subfleet is fully charged
                    if SOC_step[subfleet] > 1:
                        SOC_step[subfleet] = initSOC[subfleet]
                        power_subfleet[subfleet] = 0
                    
                # Certain amount of the vehicles of each sub fleet are charged at other places: grocery stores, restaurants, etc -> uncontrolled charging
                elif self.state_of_the_subfleet(t,subfleet) == 'other':
                    power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet]]
                    power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet]],
                                                     self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet]],
                                                     self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet]],
                                                     self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet]],power_ac)
                    ibat_charging = self.current_charging(v_oc.iloc[subfleet],R.iloc[subfleet],power_dc) 
                    Ah_rate = ibat_charging/3600
                    charge_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet]]
                    
                    # State of charge at the next time step and power of the subfleet
                    SOC_step[subfleet] = initSOC[subfleet] + charge_rate*self.ChargedAtOther_per*dt
                    power_subfleet[subfleet] = power_ac*self.ChargedAtOther_per*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet]])/1000
                    # Check if the subfleet is fully charged
                    if SOC_step[subfleet] > 1:
                        SOC_step[subfleet] = initSOC[subfleet]
                        power_subfleet[subfleet] = 0
                    
                # Hypothesis: the sub fleets are only charged at home during night or right away not in these "stops"
                elif self.state_of_the_subfleet(t,subfleet) == 'home':
                    power_subfleet[subfleet] = 0
                    
                # Charging at home after all-day trips with different charging strategies
                elif self.state_of_the_subfleet(t,subfleet) == 'home after schedule':  
                    if self.monitor_strategy[subfleet] == 'midnight':     # subfleets that start charging at midnight -> uncontrolled case
                        # time to start charging: usually at 12 AM (20*3600), but earlier may be required for some cases depending on the case
                        start_charging = 20*3600
                        SOC_step[subfleet], power_subfleet[subfleet] = self.start_charging_midnight_strategy(start_charging, t, subfleet, initSOC[subfleet], dt)
                        # Check if the subfleet is fully charged
                        if SOC_step[subfleet] > 1:
                            SOC_step[subfleet] = initSOC[subfleet]
                            power_subfleet[subfleet] = 0
                    
                    elif self.monitor_strategy[subfleet] == 'tcin':      # subfleets that start charging at a certain time to be fully charged before the tcin
                        # time to be fully charged at the next day or the current day depending on the actual time
                        if t < self.ScheduleStartTime.iloc[subfleet][1]:
                            tcin = self.ScheduleStartTime.iloc[subfleet][1]
                        else:
                            tcin = self.ScheduleStartTime.iloc[subfleet][1] + 24*3600
                        SOC_step[subfleet], power_subfleet[subfleet],_ = self.start_charging_to_meet_tcin(tcin, t, subfleet, initSOC[subfleet], dt)
                        # Check if the subfleet is fully charged
                        if SOC_step[subfleet] > 1:
                            SOC_step[subfleet] = initSOC[subfleet]
                            power_subfleet[subfleet] = 0
            
            # Calculate the total power uncontrolled            
            power_uncontrolled = np.sum(power_subfleet, axis = 0)
            
            SOC_monitor = pd.DataFrame(columns = ['SOCinit', 'state_subfleet', 'charging_strategy'])
            for subfleet in range(self.N_SubFleets):
                SOC_monitor.loc[subfleet, 'SOCinit'] = initSOC[subfleet]
                SOC_monitor.loc[subfleet, 'state_subfleet'] = self.state_of_the_subfleet(t,subfleet)
                SOC_monitor.loc[subfleet, 'charging_strategy'] = self.monitor_strategy[subfleet]
            
            # Sort the state of charge to charge the vehicles in the right away charging strategy
            SOC_sorted = SOC_monitor.sort_values('SOCinit')
                
            # Controlled case: the controlled case + the uncontrolled case must be equal to the requested power
            # Start charging the electric vehicles with the lowest state of charge
            power_controlled_thres = p_total - power_uncontrolled
            power_controlled = 0
            for subfleet in range(self.N_SubFleets):
                idx = SOC_sorted['state_subfleet'].index[subfleet]
                if SOC_sorted['state_subfleet'][idx] == 'home after schedule':
                    if SOC_sorted['charging_strategy'][idx] == 'right away':  # subfleets that start charging immediately -> controlled charging
                        # Check the time to start charging to meet tcin
                        _,_,check_tcin = self.start_charging_to_meet_tcin(tcin, t, idx, initSOC[idx], dt)
                        # If the time is less than the time when the car must be start charging to meet tcin then:
                        if t < check_tcin:
                            if power_uncontrolled >= p_total: 
                                power_demanded = power_uncontrolled  # All the right away chargers turned off
                            else:
                                SOC_step[idx], power_subfleet[idx] = self.start_charging_right_away_strategy(idx, SOC_sorted['SOCinit'][idx], dt)
                                # Check if the subfleet is fully charged
                                if SOC_step[idx] > 1:
                                    SOC_step[idx] = initSOC[idx]
                                    power_subfleet[idx] = 0
                                # Check if the controlled power is greater than our constraint
                                elif (power_controlled + power_subfleet[idx]) < power_controlled_thres:
                                    power_controlled += power_subfleet[idx]
                                else:
                                    # Surpasses the maximum power and returns the previous state
                                    power_subfleet[idx] = 0
                                    SOC_step[idx] = initSOC[idx]
                        # However, if the time is greater, we have to start charging right away regardless the service demanded (constraint of the device)
                        elif t >= check_tcin:
                            SOC_step[idx], power_subfleet[idx] = self.start_charging_right_away_strategy(idx, SOC_sorted['SOCinit'][idx], dt)
                            power_controlled += power_subfleet[idx]

            # Demand of power
            power_demanded = power_uncontrolled + power_controlled
            
            # Calculate maximum power that can be injected to the grid -> all the right away chargers are turned on
            max_power_controlled = 0
            for subfleet in range(self.N_SubFleets):
                if self.state_of_the_subfleet(t,subfleet) == 'home after schedule':  
                    if self.monitor_strategy[subfleet] == 'right away':
                        SOC_aux, power_aux = self.start_charging_right_away_strategy(subfleet, initSOC[subfleet], dt)
                        if SOC_aux < 1:
                            max_power_controlled += power_aux
                        
            #Maximum demand of power
            max_power_demanded = power_uncontrolled + max_power_controlled
            
            # Calculate the energy stored in each individual subfleet
            total_energy = 0
            for subfleet in range(self.N_SubFleets):
                R = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[subfleet]],
                                            self.df_VehicleModels['R_SOC_1'][self.SubFleetId[subfleet]],
                                            self.df_VehicleModels['R_SOC_2'][self.SubFleetId[subfleet]], SOC_step[subfleet])
                v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[subfleet]],
                                            self.df_VehicleModels['V_SOC_1'][self.SubFleetId[subfleet]],
                                            self.df_VehicleModels['V_SOC_2'][self.SubFleetId[subfleet]], 
                                            self.df_VehicleModels['Number_of_cells'][self.SubFleetId[subfleet]],SOC_step[subfleet],0,0)
                p_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet]],
                                             self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet]],
                                             self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet]],
                                             self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet]],power_subfleet[subfleet])
                ibat = self.current_charging(v_oc,R,p_dc)
                v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[subfleet]],
                                         self.df_VehicleModels['V_SOC_1'][self.SubFleetId[subfleet]],
                                         self.df_VehicleModels['V_SOC_2'][self.SubFleetId[subfleet]], 
                                         self.df_VehicleModels['Number_of_cells'][self.SubFleetId[subfleet]],SOC_step[subfleet],R,ibat)
                capacity = self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet]]
                energy_per_subfleet = self.energy_stored_per_subfleet(SOC_step[subfleet], capacity, v, self.VehiclesSubFleet)
                total_energy += energy_per_subfleet
            
            # response outputs 
            response.P_togrid  = power_demanded
            response.Q_togrid  = 0
            response.P_service = power_demanded - self.p_baseline
            response.Q_service = 0
            
            response.E = total_energy
            response.C = None
            
            response.P_togrid_max = max_power_demanded
            response.P_togrid_min = power_uncontrolled
            response.Q_togrid_max = 0
            response.Q_togrid_min = 0
            
            response.P_service_max = max_power_demanded - self.p_baseline
            response.P_service_min = power_uncontrolled - self.p_baseline
            response.Q_service_max = 0
            response.Q_service_min = 0
            
            response.P_dot_up   = 0
            response.P_dot_down = 0
            response.Q_dot_up   = 0
            response.Q_dot_down = 0
            

            response.Eff_charge    = 0  
            response.Eff_discharge = 0
    
            response.dT_hold_limit = None
            response.T_restore     = None
    
            response.Strike_price = None
            response.SOC_cost     = None
            
            self.SOC = SOC_step
            self.time = t + dt
            # Restart time if it surpasses 24 hours
            if self.time > 24*3600:
                self.time = self.time - 24*3600
         
            # Check the outputs
            return response
    
    def forecast(self, requests):
        """
        Request for current timestep

        :param requests: list of  requests

        :return res: list of FleetResponse
        """
        
        SOC_aux = self.SOC
        responses = []
        for req in requests:
            FleetResponse = self.simulate(req.P_req, req.Q_req, self.SOC, self.time, req.sim_step)
            res = FleetResponse
            responses.append(res)     
        # restart the state of charge
        self.SOC = SOC_aux
        
        return responses
    
    def state_of_the_subfleet(self,t_secs,subfleet_number):
        """ Method to specify the state of the subfleet: driving, work, other, home after schedule, home """
        if t_secs > max(self.ScheduleEndTime.iloc[subfleet_number]) or t_secs < self.ScheduleStartTime.iloc[subfleet_number][1]:
            return 'home after schedule'
        else:
            for i in range(np.min(np.shape(self.SchedulePurpose.iloc[subfleet_number]))): 
                if t_secs < self.ScheduleEndTime.iloc[subfleet_number][i+1] and t_secs > self.ScheduleStartTime.iloc[subfleet_number][i+1]:
                    return 'driving' 
                elif self.SchedulePurpose.iloc[subfleet_number][i+1] == 2 and t_secs < self.ScheduleStartTime.iloc[subfleet_number][i+2]: 
                    return 'work'
                elif self.SchedulePurpose.iloc[subfleet_number][i+1] == 1.5 and t_secs < self.ScheduleStartTime.iloc[subfleet_number][i+2]: 
                    return 'other'
                elif self.SchedulePurpose.iloc[subfleet_number][i+1] == 1.0 and t_secs < self.ScheduleStartTime.iloc[subfleet_number][i+2]: 
                    return 'home'
                      
    def trip_identification(self,t_secs,subfleet_number):
        """ Method to identify the trip of the day and returns the trip id """
        for trip_id in range(np.min(np.shape(self.SchedulePurpose.iloc[subfleet_number]))): 
            if t_secs < self.ScheduleEndTime.iloc[subfleet_number][trip_id+1] and t_secs > self.ScheduleStartTime.iloc[subfleet_number][trip_id+1]:
                return trip_id
            
    def average_speed_of_trip_miles_per_second(self,subfleet_number,trip_id):
        """ average speed of the trip expressed in miles per second """
        t = self.ScheduleEndTime.iloc[subfleet_number][trip_id+1] - self.ScheduleStartTime.iloc[subfleet_number][trip_id+1]
        miles = self.ScheduleMiles.iloc[subfleet_number][trip_id+1]
        return miles/t

    def voltage_battery(self,v0,v1,v2,cells,SOC,R,current_bat):
        """ Voltage as a function of the State of Charge of the battery, the resistance, and the current"""
        return cells*(v0 + v1*SOC + v2*SOC**2 + R*current_bat)
    
    def resistance_battery(self,r0,r1,r2,SOC):
        """ Resistance as a function of the State of Charge of the battery """
        return r0 + r1*SOC + r2*SOC**2

    def range_subfleet(self,Ah_usable,Voltage, Wh_mi, SOC):
        """ Method to calculate the range for a given electric vehicle model """
        return SOC*Ah_usable*Voltage/Wh_mi
    
    def power_dc_charger(self, a0, a1, a2, power_ac_max, power_ac):
        """ Method to calculate DC power in the charger as a function of the losses and the maximum AC power of the charger """
        if power_ac < power_ac_max:
            return power_ac - (a0 + a1*power_ac + a2*power_ac**2)
        else:
            return power_ac_max - (a0 + a1*power_ac_max + a2*power_ac_max**2)
    
    def current_charging(self,v_oc,R,power_dc):
        """ Method to calculate the current to charge the battery as a function of the V_OC, P_DC, internal resistance of the battery """
        return (v_oc - np.sqrt(v_oc**2 - 4*R*power_dc))/(2.*R)   
    
    def energy_stored_per_subfleet(self, SOC, v, Ah_nom, n_vehicles_subfleet):
        """ Method to calculate energy stored of each sub fleet """
        return SOC*Ah_nom*v*n_vehicles_subfleet/1000
        
    def match_schedule(self, seed, SOC, V):
        """ Method to match the schedule of each sub fleet from NHTS data"""
        
        #fix pseudorandom numbers
        np.random.seed(seed)
        
        # Daily range of each subfleet based on the Weibull distribution and the features of the vehicle models
        SubFleetRange = self.range_subfleet(self.df_VehicleModels['Ah_usable'][self.SubFleetId],V,
                                            self.df_VehicleModels['Wh_mi'][self.SubFleetId],SOC)*self.lambd*np.random.weibull(self.a,self.N_SubFleets)
        # Daily range from the NHTS survey
        Miles = self.df_Miles.drop(self.df_Miles.columns[0], axis = 1)
        NHTS_DailyRange = Miles.sum(axis = 1)
        
        # Matching the Schedule
        # Assign the Range of each subfleet
        idx = np.zeros([self.N_SubFleets,], dtype = int)
        for i in range(self.N_SubFleets):
            idx[i] = (NHTS_DailyRange - SubFleetRange.iloc[i]).abs().idxmin()
        # Remove the first column of each dataset      
        StartTime = self.df_StartTime.drop(self.df_StartTime.columns[0], axis = 1)
        EndTime   = self.df_EndTime.drop(self.df_EndTime.columns[0], axis = 1)
        WhyTo     = self.df_WhyTo.drop(self.df_WhyTo.columns[0], axis = 1).iloc[idx]
        Miles     = Miles.iloc[idx]
        # Transform the times into seconds and substitute negative values by 0: referenced to 4 AM
        StartTime_secs = ((StartTime.iloc[idx] - 400)/100)*3600
        EndTime_secs   = ((EndTime.iloc[idx] - 400)/100)*3600
        StartTime_secs = StartTime_secs.mask(StartTime_secs < 0, 0)
        EndTime_secs   = EndTime_secs.mask(EndTime_secs < 0, 0)
    
        # Miles per each subfleet
        MilesSubfleet = NHTS_DailyRange.iloc[idx]
    
        # Purpose of the travel: 1 is at home, 2 is at work, 1.5 is other 
        Purpose = WhyTo.replace(to_replace = [1, 11, 13], value = [1, 2, 2])
        Purpose = Purpose.mask(Purpose > 11, 1.5)
    
        return StartTime_secs, EndTime_secs, Miles, Purpose, MilesSubfleet
       
    def start_charging_midnight_strategy(self, charge_programmed, t_secs, subfleet_number, SOC, dt):
        """ Method to calculate the start-charging-at-midnight strategy """
        if t_secs > charge_programmed:
            v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[subfleet_number]],
                                     self.df_VehicleModels['V_SOC_1'][self.SubFleetId[subfleet_number]],
                                     self.df_VehicleModels['V_SOC_2'][self.SubFleetId[subfleet_number]], 
                                     self.df_VehicleModels['Number_of_cells'][self.SubFleetId[subfleet_number]],SOC,0,0)
            R = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[subfleet_number]],
                                        self.df_VehicleModels['R_SOC_1'][self.SubFleetId[subfleet_number]],
                                        self.df_VehicleModels['R_SOC_2'][self.SubFleetId[subfleet_number]], SOC)
            power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]]
            power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet_number]],
                                             self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet_number]],
                                             self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet_number]],
                                             self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]],power_ac)
            ibat_charging = self.current_charging(v,R,power_dc) 
            Ah_rate = ibat_charging/3600
            charge_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet_number]]
            SOC_step = SOC + charge_rate*dt
            
            return SOC_step, power_ac*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet_number]])/1000
        else:
            return SOC, 0
        
    def start_charging_to_meet_tcin(self, tcin, t_secs, subfleet_number, SOC, dt):
        """ Method to calculate the start-charging-to-be-fully-charged strategy """
        # This can be different for more complicated models
        hours_before = 1
        time_fully_charged = tcin - hours_before*3600
        
        v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[subfleet_number]],
                                 self.df_VehicleModels['V_SOC_1'][self.SubFleetId[subfleet_number]],
                                 self.df_VehicleModels['V_SOC_2'][self.SubFleetId[subfleet_number]], 
                                 self.df_VehicleModels['Number_of_cells'][self.SubFleetId[subfleet_number]],SOC,0,0)
        R = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['R_SOC_1'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['R_SOC_2'][self.SubFleetId[subfleet_number]], SOC)
        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]]
        power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet_number]],
                                         self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet_number]],
                                         self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet_number]],
                                         self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]],power_ac)
        ibat_charging = self.current_charging(v,R,power_dc) 
        Ah_rate = ibat_charging/3600
        charge_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet_number]]
        
        # Calculate that the car should start charging to be fully charged certain time before the tcin
        delta_SOC = 1 - SOC
        time_start_charging = int(time_fully_charged - (delta_SOC/charge_rate))
        
        if t_secs >= time_start_charging:
            SOC_step = SOC + charge_rate*dt
            return SOC_step, power_ac*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet_number]])/1000, time_start_charging
        else:
            return SOC, 0, time_start_charging
        
    def start_charging_right_away_strategy(self, subfleet_number, SOC, dt):
        """ Method to calculate the start-charging-right-away strategy """
        v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[subfleet_number]],
                                 self.df_VehicleModels['V_SOC_1'][self.SubFleetId[subfleet_number]],
                                 self.df_VehicleModels['V_SOC_2'][self.SubFleetId[subfleet_number]], 
                                 self.df_VehicleModels['Number_of_cells'][self.SubFleetId[subfleet_number]],SOC,0,0)
        R = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['R_SOC_1'][self.SubFleetId[subfleet_number]],
                                    self.df_VehicleModels['R_SOC_2'][self.SubFleetId[subfleet_number]], SOC)
        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]]
        power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[subfleet_number]],
                                         self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[subfleet_number]],
                                         self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[subfleet_number]],
                                         self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[subfleet_number]],power_ac)
        ibat_charging = self.current_charging(v,R,power_dc) 
        Ah_rate = ibat_charging/3600
        charge_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[subfleet_number]]
        SOC_step = SOC + charge_rate*dt
        
        return SOC_step, power_ac*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[subfleet_number]])/1000
        
    
    def change_config(self, **kwargs):
        """
        This function is here for future use. The idea of having it is for a service to communicate with a fleet
        in a nondeterministic manner during a simulation

        :param kwargs: a dictionary of (key, value) pairs. The exact keys are decided by a fleet.

        Example: Some fleets can operate in an autonomous mode, where they're not responding to requests,
        but watching, say, the voltage. If the voltage dips below some defined threshold (which a service might define),
        then the fleet responds in a pre-defined way.
        In this example, the kwargs can be {"voltage_threshold": new_value}
        """
        pass