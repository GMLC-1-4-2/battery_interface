# -*- coding: utf-8 -*-
"""
Description: It contains the interface to interact with the fleet of electric 
vehicles: ElectricVehiclesFleet

Last update: 10/24/2018
Version: 1.0
Author: afernandezcanosa@anl.gov
"""

from fleet_interface import FleetInterface
from fleet_request   import FleetRequest
from fleet_response  import FleetResponse
from frequency_droop import FrequencyDroop

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
from scipy.stats import truncnorm
import csv

class ElectricVehiclesFleet(FleetInterface):
    
    def __init__(self, GridInfo, ts):
        """
        Constructor
        """
        # Run baseline power to store baseline power and SOC if parameters 
        # of the fleet are changed. ONLY ASSIGN TRUE IF YOU CHANGE THE 
        # PARAMETERS OF THE FLEET AS IT WILL DRAMATICALLY INCREASE THE CPU TIME
        self.run_baseline = False
        self.n_days_base = 10
        # Establish the properties of the grid on which the fleet is connected on
        self.grid = GridInfo
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
        # Random seed for matching schedule and getting charging strategies
        self.seed = 0
        np.random.seed(self.seed)
        
        # Read data from NHTS survey      
        self.df_Miles     = pd.read_table(os.path.join(dirname,'data/TRPMILES_filt.txt'), delim_whitespace=True, header=None)
        self.df_StartTime = pd.read_table(os.path.join(dirname,'data/STRTTIME_filt.txt'), delim_whitespace=True, header=None)
        self.df_EndTime   = pd.read_table(os.path.join(dirname,'data/ENDTIME_filt.txt') , delim_whitespace=True, header=None)
        self.df_WhyTo     = pd.read_table(os.path.join(dirname,'data/WHYTO_filt.txt' )  , delim_whitespace=True, header=None)
        
        # Percentage of cars that are charged at work/other places: Statistical studies from real data
        self.ChargedAtWork_per  = 0.17
        self.ChargedAtOther_per = 0.02

        # Initialize timestamps and local times of the class for future calculations
        self.initial_ts = ts 
        self.ts = ts
        self.initial_time = self.get_time_of_the_day(ts)
        self.time = self.get_time_of_the_day(ts)
        self.dt = 1
        
        # Mix of charging strategies: charging right away, start charging at midnight, start charging to be fully charged before the TCIN (percentage included)
        self.strategies = [ ['right away', 'midnight', 'tcin'], [0.4, 0.3, 0.3] ]
        # Charging strategy corresponding to each sub fleet
        self.monitor_strategy = []
        for i in range(len(self.strategies[0])):
            self.monitor_strategy = self.monitor_strategy + [self.strategies[0][i]]*int(self.strategies[1][i]*self.N_SubFleets)
        # Randomize strategies among all the sub fleets    
        np.random.shuffle(self.monitor_strategy)
        
        # Baseline simulations
        if self.run_baseline == True:
            self.run_baseline_simulation()
        # Read the SOC curves from baseline Montecarlo simulations of the different charging strategies
        self.df_SOC_curves = pd.read_csv(os.path.join(dirname,'data/SOC_curves_charging_modes.csv' ))
        
        # Read the baseline power from Montecarlo simulations of the different charging strategies
        self.df_baseline_power = pd.read_csv(os.path.join(dirname,'data/power_baseline_charging_modes.csv' ))
        self.p_baseline = (self.strategies[1][0]*self.df_baseline_power['power_RightAway_kW'].iloc[self.initial_time] + 
                           self.strategies[1][1]*self.df_baseline_power['power_Midnight_kW'].iloc[self.initial_time] + 
                           self.strategies[1][2]*self.df_baseline_power['power_TCIN_kW'].iloc[self.initial_time])

        # Initial state of charge of all the subfleets => Depends on the baseline simulations (SOC curves)
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
        self.ScheduleStartTime, self.ScheduleEndTime, self.ScheduleMiles, self.SchedulePurpose, self.ScheduleTotalMiles = self.match_schedule(self.seed,self.SOC,self.Voltage)
        
        """
        Can this fleet operate in autonomous operation?
        """
        
        # Locations of the subfleets: suppose that you only have two locations
        self.location = np.random.randint(0,2,self.N_SubFleets)
        
        # Fleet configuration variables
        self.is_P_priority = True
        self.is_autonomous = False
        
        # Autonomous operation
        self.FW21_Enabled = True
        if self.FW21_Enabled == True:
            # Single-sided deadband value for low-frequency, in Hz
            db_UF = 0.036
            # Single-sided deadband value for high-frequency, in Hz
            db_OF = 0.036
            # Per-unit frequency change corresponding to 1 per-unit power output change (frequency droop), dimensionless
            k_UF  = 0.05
            # Per-unit frequency change corresponding to 1 per-unit power output change (frequency droop), dimensionless
            k_OF  = 0.05
            # Available active power, in p.u. of the DER rating
            P_avl = 1.0
            # Minimum active power output due to DER prime mover constraints, in p.u. of the DER rating
            P_min = 0.0
            P_pre = 1.0
            self.fw_function = FrequencyDroop(db_UF, db_OF, k_UF, k_OF, P_avl, P_min, P_pre)
        
        # Impact metrics of the fleet
        # End of life cost
        self.eol_cost = 6000
        # Cylce life
        self.cycle_life = 1e3
        # State of health of the battery for all the subfleets
        self.soh_init = np.repeat(100.0, self.N_SubFleets)
        self.soh = np.repeat(100.0, self.N_SubFleets)
        # Energy efficiency
        self.energy_efficiency = 0.9
        
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
        This function takes the fleet request and repackages it for the 
        internal simulate method of the class

        :param fleet_request: an instance of FleetRequest

        :return res: an instance of FleetResponse
        """
        # call simulate method with proper inputs
        FleetResponse = self.simulate(fleet_request.P_req, fleet_request.Q_req, self.SOC, self.time, self.dt)

        return FleetResponse
    
    def frequency_watt(self, p_req = 0,ts=datetime.utcnow(),location=0):
        """
        This function takes the requested power, date, time, and location
        and modifies the requested power according to the configured FW21 
        :param p_req: real power requested, ts:datetime object,
               location: numerical designation for the location of the BESS
        :return p_mod: modified real power based on FW21 function
        """
        f = self.grid.get_frequency(ts,location)
        self.fw_function.P_pre = p_req
        p_mod = self.fw_function.F_W(f) 
        return p_mod
    
    def update_soc_due_to_frequency_dropp(self, initSOC, SOC, p_tot, p_mod):
        """
        This method returns the modified state of charge of each subfleet 
        due to frequency droop in the grid
        """
        if p_tot !=0:
            SOC_update = initSOC + (p_mod/p_tot)*(SOC - initSOC)
        else:
            SOC_update = initSOC
           
        return SOC_update
    
    def simulate(self, P_req, Q_req, initSOC, t, dt):
        """ 
        Simulation part of the code: charge, discharge, ...:
        everything must be referenced to baseline power from Montecarlo 
        simulations of the different charging strategies
        """

        # Baseline power is extracted from baseline simulations
        self.p_baseline = (self.strategies[1][0]*self.df_baseline_power['power_RightAway_kW'].iloc[self.time] + 
                           self.strategies[1][1]*self.df_baseline_power['power_Midnight_kW'].iloc[self.time] + 
                           self.strategies[1][2]*self.df_baseline_power['power_TCIN_kW'].iloc[self.time])

        # The total power requested must be referenced to the baseline power
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
                        if t < self.ScheduleStartTime.iloc[idx][1]:
                            tcin = self.ScheduleStartTime.iloc[idx][1]
                        else:
                            tcin = self.ScheduleStartTime.iloc[idx][1] + 24*3600
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
                            # Check if the subfleet is fully charged
                            if SOC_step[idx] > 1:
                                SOC_step[idx] = initSOC[idx]
                                power_subfleet[idx] = 0
            
            """
            Modify the power and SOC of the different subfeets according 
            to the frequency droop regulation according to IEEE standard
            """
            power_aux = power_subfleet
            for subfleet in range(self.N_SubFleets):
                if self.state_of_the_subfleet(t,subfleet) == 'home after schedule':
                    if self.FW21_Enabled == True and self.is_autonomous == True:
                        # Update the power
                        power_subfleet[subfleet] = power_subfleet[subfleet]*self.frequency_watt(
                                power_subfleet[subfleet],
                                self.ts,
                                self.location[subfleet])
                        # Update the state of charge of the batteries of the different subfleets
                        SOC_step[subfleet] = self.update_soc_due_to_frequency_dropp(
                                initSOC[subfleet],
                                SOC_step[subfleet],
                                power_aux[subfleet],
                                power_subfleet[subfleet])
                    else:
                        break

            # Demand of power
            power_demanded = np.sum(power_subfleet, axis = 0)
            
            # Calculate maximum power that can be injected to the grid -> all the right away chargers are turned on
            for subfleet in range(self.N_SubFleets):
                if self.state_of_the_subfleet(t,subfleet) == 'home after schedule':  
                    if self.monitor_strategy[subfleet] == 'right away':
                        SOC_check, power_subfleet[subfleet] = self.start_charging_right_away_strategy(subfleet, initSOC[subfleet], dt)
                        if self.FW21_Enabled == True and self.is_autonomous == True:
                            # Update the power
                            power_subfleet[subfleet] = power_subfleet[subfleet]*self.frequency_watt(
                                    power_subfleet[subfleet],
                                    self.ts,
                                    self.location[subfleet])
                        if SOC_check > 1:
                            power_subfleet[subfleet] = 0

                        
            # Maximum demand of power
            max_power_demanded = np.sum(power_subfleet, axis = 0)
            
            # Calculate the energy stored in each individual subfleet
            total_energy = 0
            energy_per_subfleet = np.zeros([self.N_SubFleets,])
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
                energy_per_subfleet[subfleet] = self.energy_stored_per_subfleet(SOC_step[subfleet], capacity, v, self.VehiclesSubFleet)
                total_energy += energy_per_subfleet[subfleet]
            
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
            self.ts = self.ts + timedelta(dt)
            # Restart time if it surpasses 24 hours
            if self.time > 24*3600:
                self.time = self.time - 24*3600
                
            # Update the state of health of the batteries of each subfleet
            for subfleet in range(self.N_SubFleets):
                self.soh[subfleet] = (self.soh[subfleet] - 
                                100*(dt/3600)*abs(power_subfleet[subfleet]) / 
                                ((1+1/self.energy_efficiency)*self.cycle_life*energy_per_subfleet[subfleet]))
         
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
        if t_secs >= charge_programmed:
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
        """ 
        Method to calculate the start-charging-right-away strategy
        """
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

    def run_baseline_simulation(self):
        """ 
        Method to run baseline simulation and store power level and SOC of 
        the sub fleets.
        """
        n_days_base = self.n_days_base
        sim_time = 24*3600
        
        print("Running baseline simulation ...")       
        print("Running baseline right away charging strategy ...")
        soc_1, power_base_1, soc_std_1 = self.run_baseline_right_away(n_days_base, sim_time)
        
        print("Running baseline midnight charging strategy ...")
        soc_2, power_base_2, soc_std_2 = self.run_baseline_midnight(n_days_base, sim_time)
        
        print("Running baseline tcin charging strategy ... ")
        soc_3, power_base_3, soc_std_3 = self.run_baseline_tcin(n_days_base, sim_time)
       
        print("Exporting baseline soc and power ...")
        # Dataframe to import the initial soc of the sub fleets with the aim to initialize the class
        data_soc = {'time': np.linspace(0,sim_time-1,sim_time),
                    'SOC_mean_RightAway': soc_1, 'SOC_std_RightAway': soc_std_1,
                    'SOC_mean_Midnight': soc_2, 'SOC_std_Midnight': soc_std_2,
                    'SOC_mean_TCIN': soc_3, 'SOC_std_TCIN': soc_std_3}           
        df_soc = pd.DataFrame(data=data_soc, columns=['time',
                                                      'SOC_mean_RightAway', 'SOC_std_RightAway',
                                                      'SOC_mean_Midnight', 'SOC_std_Midnight',
                                                      'SOC_mean_TCIN', 'SOC_std_TCIN'])   
        
        df_soc[['SOC_std_RightAway', 'SOC_std_Midnight', 'SOC_std_TCIN']] = \
        df_soc[['SOC_std_RightAway', 'SOC_std_Midnight', 'SOC_std_TCIN']].replace(0,0.02)

        # Dataframe to import the baseline power with the aim to provide service power
        data_power = {'time': np.linspace(0,2*sim_time-1,2*sim_time),
                           'power_RightAway_kW': np.hstack((power_base_1*1e-3, power_base_1*1e-3)),
                           'power_Midnight_kW': np.hstack((power_base_2*1e-3, power_base_2*1e-3)),
                           'power_TCIN_kW': np.hstack((power_base_3*1e-3, power_base_3*1e-3))}            
        df_power = pd.DataFrame(data = data_power, columns = ['time', 
                                                              'power_RightAway_kW',
                                                              'power_Midnight_kW',
                                                              'power_TCIN_kW'])
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname,'data')
        
        df_soc.to_csv(os.path.join(path, r'SOC_curves_charging_modes.csv'), index = False)
        df_power.to_csv(os.path.join(path, r'power_baseline_charging_modes.csv'), index = False)
        print("Exported")
        
    def discharge_baseline(self, StartTime_secs, EndTime_secs, Miles, Purpose, MilesSubfleet, SOC, SOC_sf, sim_time, power_ac, v):
        """ Method to compute discharging for the baseline case """
        power_ac_demanded = np.zeros([self.N_SubFleets,sim_time])
        rate_dis = np.array(self.df_VehicleModels['Wh_mi'][self.SubFleetId]/(v*self.df_VehicleModels['Ah_usable'][self.SubFleetId]))
        j_full_charge = np.zeros([self.N_SubFleets,], dtype = int)
        time_full_charge = np.zeros([self.N_SubFleets,], dtype = int)
        SOC_time = np.zeros([self.N_SubFleets, sim_time])
        
        for i in range(self.N_SubFleets):
            SOC_time[i][0:int(StartTime_secs.iloc[i][1])] = SOC[i]
            for k in range(np.min(np.shape(Purpose.iloc[i]))):
                if Purpose.iloc[i][k+1] > 0:
                    # Sub fleet is driving
                    t1 = int(EndTime_secs.iloc[i][k+1]) - int(StartTime_secs.iloc[i][k+1])
                    if t1 <= 0:
                        t1 = 1
                    # Discharging
                    SOC_time[i][int(StartTime_secs.iloc[i][k+1]):int(EndTime_secs.iloc[i][k+1])] = np.linspace(SOC[i], SOC[i]-rate_dis[i]*Miles.iloc[i][k+1], t1)
                    SOC_sf[i] = SOC_sf[i] - rate_dis[i]*Miles.iloc[i][k+1]
                    power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[i]],
                                                     power_ac.iloc[i])
                    v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[i]],
                                                self.df_VehicleModels['V_SOC_1'][self.SubFleetId[i]],
                                                self.df_VehicleModels['V_SOC_2'][self.SubFleetId[i]], 
                                                self.df_VehicleModels['Number_of_cells'][self.SubFleetId[i]], SOC_time[i][int(EndTime_secs.iloc[i][k+1])], 0, 0)       
                    r_batt = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['R_SOC_1'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['R_SOC_2'][self.SubFleetId[i]], SOC_time[i][int(EndTime_secs.iloc[i][k+1])])            
                    i_batt = self.current_charging(v_oc,r_batt,power_dc)
                    Ah_rate = i_batt/3600
                    charging_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[i]]                        
                    # Charging at work
                    if Purpose.iloc[i][k+1] == 2:
                        t = int(StartTime_secs.iloc[i][k+2]) - int(EndTime_secs.iloc[i][k+1])
                        SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])] = np.linspace(SOC_sf[i],
                                SOC_sf[i] + self.ChargedAtWork_per*charging_rate*t, t)
                        if any(SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])] >= 1):
                            j_full_charge[i] = (1 - pd.Series(SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])])).abs().idxmin()
                            time_full_charge[i] = j_full_charge[i] + int(EndTime_secs.iloc[i][k+1])
                            SOC_time[i][time_full_charge[i]:sim_time] = 1
                            
                        SOC_sf[i] = SOC_time[i][int(StartTime_secs.iloc[i][k+2])-1]
                        power_ac_demanded[i][int(EndTime_secs.iloc[i][k+1]):
                            int(StartTime_secs.iloc[i][k+2])] = power_ac.iloc[i]*\
                            self.ChargedAtWork_per*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[i]])                         
                    # Charging at other places    
                    elif Purpose.iloc[i][k+1] == 1.5:
                        t = int(StartTime_secs.iloc[i][k+2]) - int(EndTime_secs.iloc[i][k+1])
                        SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])] = np.linspace(SOC_sf[i], SOC_sf[i] + self.ChargedAtOther_per*charging_rate*t, t)
                        if any(SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])] >= 1):
                            j_full_charge[i] = (1 - pd.Series(SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])])).abs().idxmin()
                            time_full_charge[i] = j_full_charge[i] + int(EndTime_secs.iloc[i][k+1])
                            SOC_time[i][time_full_charge[i]:sim_time] = 1
                            
                        SOC_sf[i] = SOC_time[i][int(StartTime_secs.iloc[i][k+2])-1]
                        power_ac_demanded[i][int(EndTime_secs.iloc[i][k+1]):
                            int(StartTime_secs.iloc[i][k+2])] = power_ac.iloc[i]*\
                            self.ChargedAtOther_per*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[i]])
                                  
                    elif Purpose.iloc[i][k+1] == 1.0:
                        SOC_time[i][int(EndTime_secs.iloc[i][k+1]):int(StartTime_secs.iloc[i][k+2])] = SOC_sf[i]                           
                else:
                    # Again, at home!
                    SOC_time[i][int(EndTime_secs.iloc[i][k]):sim_time] = SOC_sf[i]
                    break
                
        return SOC_time, SOC_sf, power_ac_demanded
 
    def run_baseline_right_away(self, n_days_base, sim_time):
        """ Method to run baseline with charging right away strategy """
        baseline_power = np.zeros([sim_time, ])
        baseline_soc = np.zeros([sim_time, ])   
        baseline_std_soc = np.zeros([sim_time, ]) 
        # Initial SOC of the sub fleets
        SOC = np.ones([self.N_SubFleets,])
        SOC_sf = SOC
        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId]
        power_dc = np.zeros([self.N_SubFleets,])
        
        for day in range(n_days_base):
            print("Day %i" %(day+1))
            
            v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                 self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                 self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                 self.df_VehicleModels['Number_of_cells'][self.SubFleetId],SOC,0,0)    
            StartTime_secs, EndTime_secs, Miles, Purpose, MilesSubfleet = self.match_schedule(day,SOC,v)                    
            SOC_time, SOC_sf, power_ac_demanded =\
                self.discharge_baseline(StartTime_secs, EndTime_secs, Miles,
                                        Purpose, MilesSubfleet, SOC, SOC_sf,
                                        sim_time, power_ac, v)
                
            # CHARGING STRATEGY   
            time_arrival_home = np.max(EndTime_secs, axis = 1)
            SOC_arrival_home = SOC_sf
            
            for i in range(self.N_SubFleets):
                power_dc[i] = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[i]],
                                                    self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[i]],
                                                    self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[i]],
                                                    self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[i]],
                                                    power_ac.iloc[i])
            v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                        self.df_VehicleModels['Number_of_cells'][self.SubFleetId], SOC_arrival_home, 0, 0)       
            r_batt = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId],
                                             self.df_VehicleModels['R_SOC_1'][self.SubFleetId],
                                             self.df_VehicleModels['R_SOC_2'][self.SubFleetId], SOC_arrival_home)            
            i_batt = self.current_charging(v_oc,r_batt,power_dc)
            Ah_rate = i_batt/3600
            charging_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId]
            j_full_charge = np.zeros([self.N_SubFleets,], dtype = int)
            time_full_charge = np.zeros([self.N_SubFleets,], dtype = int)
            for i in range(self.N_SubFleets):
                t = sim_time - int(time_arrival_home.iloc[i])
                SOC_time[i][int(time_arrival_home.iloc[i]):sim_time] = np.linspace(SOC_arrival_home[i],SOC_arrival_home[i] + t*charging_rate.iloc[i], t)
                j_full_charge[i] = (1 - pd.Series(SOC_time[i][int(time_arrival_home.iloc[i]):sim_time])).abs().idxmin()
                time_full_charge[i] = j_full_charge[i] + int(time_arrival_home.iloc[i])
                SOC_time[i][time_full_charge[i]:sim_time] = 1
                
                power_ac_demanded[i][int(time_arrival_home.iloc[i]):time_full_charge[i]] = power_ac.iloc[i]*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[i]])
            
            SOC = SOC_time[:,-1]
            SOC_sf = SOC
            
            baseline_power = baseline_power + power_ac_demanded.sum(axis = 0)
            baseline_soc = baseline_soc + SOC_time.mean(axis = 0)
            baseline_std_soc = baseline_std_soc + SOC_time.std(axis = 0)
                    
        return baseline_soc/n_days_base, baseline_power/n_days_base, baseline_std_soc/n_days_base    
 
    def run_baseline_midnight(self, n_days_base, sim_time):
        """ Method to run baseline with midnight charging strategy """
        baseline_power = np.zeros([sim_time, ])
        baseline_soc = np.zeros([sim_time, ])  
        baseline_std_soc = np.zeros([sim_time, ])
        # Initial SOC of the sub fleets
        SOC = np.ones([self.N_SubFleets,])
        SOC_sf = SOC
        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId]
        power_dc = np.zeros([self.N_SubFleets,])
        
        for day in range(n_days_base):
            print("Day %i" %(day+1))
            
            v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                 self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                 self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                 self.df_VehicleModels['Number_of_cells'][self.SubFleetId],SOC,0,0)    
            StartTime_secs, EndTime_secs, Miles, Purpose, MilesSubfleet = self.match_schedule(day,SOC,v)                    
            SOC_time, SOC_sf, power_ac_demanded =\
                self.discharge_baseline(StartTime_secs, EndTime_secs, Miles,
                                        Purpose, MilesSubfleet, SOC, SOC_sf,
                                        sim_time, power_ac, v)
            
            # CHARGING STRATEGY   
            time_start_charging = 20*3600*pd.Series(np.ones([self.N_SubFleets, ]))
            SOC_arrival_home = SOC_sf
            for i in range(self.N_SubFleets):
                power_dc[i] = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[i]],
                                                     power_ac.iloc[i])
            v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                        self.df_VehicleModels['Number_of_cells'][self.SubFleetId], SOC_arrival_home, 0, 0)       
            r_batt = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId],
                                             self.df_VehicleModels['R_SOC_1'][self.SubFleetId],
                                             self.df_VehicleModels['R_SOC_2'][self.SubFleetId], SOC_arrival_home)            
            i_batt = self.current_charging(v_oc,r_batt,power_dc)
            Ah_rate = i_batt/3600
            charging_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId]
            j_full_charge = np.zeros([self.N_SubFleets,], dtype = int)
            time_full_charge = np.zeros([self.N_SubFleets,], dtype = int)
            for i in range(self.N_SubFleets):
                t = sim_time - int(time_start_charging.iloc[i])
                SOC_time[i][int(time_start_charging.iloc[i]):sim_time] = np.linspace(SOC_arrival_home[i],SOC_arrival_home[i] + t*charging_rate.iloc[i], t)
                if SOC_time[i][-1] > 1:
                    j_full_charge[i] = (1 - pd.Series(SOC_time[i][int(time_start_charging.iloc[i]):sim_time])).abs().idxmin()
                    time_full_charge[i] = j_full_charge[i] + int(time_start_charging.iloc[i])
                    SOC_time[i][time_full_charge[i]:sim_time] = 1
                
                power_ac_demanded[i][int(time_start_charging.iloc[i]):time_full_charge[i]] =\
                    power_ac.iloc[i]*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[i]])
            
            SOC = SOC_time[:,-1]
            SOC_sf = SOC
            
            baseline_power = baseline_power + power_ac_demanded.sum(axis = 0)
            baseline_soc = baseline_soc + SOC_time.mean(axis = 0)
            baseline_std_soc = baseline_std_soc + SOC_time.std(axis = 0)
                    
        return baseline_soc/n_days_base, baseline_power/n_days_base, baseline_std_soc/n_days_base    

    def run_baseline_tcin(self, n_days_base, sim_time):
        """ Method to run baseline with one hour before the tcin charging strategy """

        baseline_power = np.zeros([sim_time, ])
        baseline_soc = np.zeros([sim_time, ])
        baseline_std_soc = np.zeros([sim_time, ])
        # Initial SOC of the sub fleets
        SOC = np.ones([self.N_SubFleets,])
        SOC_sf = SOC    
        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId]
        power_dc_arr = np.zeros([self.N_SubFleets, ])
        # One hour before the tcin, the sub fleets must be fully charged        
        hours_before = 1
                    
        v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                 self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                 self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                 self.df_VehicleModels['Number_of_cells'][self.SubFleetId],SOC,0,0)    
        StartTime_secs, EndTime_secs, Miles, Purpose, MilesSubfleet = self.match_schedule(0,SOC,v)
        
        time_charge_morning = np.zeros([self.N_SubFleets,], dtype = int)
        power_ac = self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId]
        
        for day in range(n_days_base+1):
            if day == 0:
                print("Burn-in day")
            else:
                print("Day %i" %(day))
            
            SOC_time_morning = np.zeros([self.N_SubFleets, sim_time])
            power_ac_demanded = np.zeros([self.N_SubFleets, sim_time])
            
            for i in range(self.N_SubFleets):
                if SOC_sf[i] < 1:
                    power_dc = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[i]],
                                                     power_ac.iloc[i])
                    v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId[i]],
                                                self.df_VehicleModels['V_SOC_1'][self.SubFleetId[i]],
                                                self.df_VehicleModels['V_SOC_2'][self.SubFleetId[i]], 
                                                self.df_VehicleModels['Number_of_cells'][self.SubFleetId[i]], SOC_sf[i], 0, 0) 
                    r_batt = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['R_SOC_1'][self.SubFleetId[i]],
                                                     self.df_VehicleModels['R_SOC_2'][self.SubFleetId[i]], SOC_sf[i])
                    i_batt = self.current_charging(v_oc,r_batt,power_dc)
                    Ah_rate = i_batt/3600
                    charging_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId[i]]
                    
                    t = int(StartTime_secs.iloc[i][1]) - hours_before*3600 - time_charge_morning[i]
                    if time_charge_morning[i] > 0:
                        SOC_time_morning[i][0:time_charge_morning[i]] = SOC_sf[i]
                        SOC_time_morning[i][time_charge_morning[i]:int(StartTime_secs.iloc[i][1]) - hours_before*3600] = np.linspace(SOC_sf[i], SOC_sf[i] + t*charging_rate,t)
                        
                    else:
                        SOC_time_morning[i][0:int(StartTime_secs.iloc[i][1]) - hours_before*3600] = np.linspace(SOC_sf[i], SOC_sf[i] + t*charging_rate,t)                       
                    
                    SOC_sf[i] = SOC_time_morning[i][int(StartTime_secs.iloc[i][1]) - hours_before*3600-1]
                    SOC_time_morning[i][int(StartTime_secs.iloc[i][1]) - hours_before*3600:int(StartTime_secs.iloc[i][1])] = 1
                    power_ac_demanded[i][time_charge_morning[i]:int(StartTime_secs.iloc[i][1]) - hours_before*3600] = power_ac.iloc[i]*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[i]])

                else:
                    SOC_time_morning[i][0:int(StartTime_secs.iloc[i][1])] = SOC_sf[i]
                    
                SOC_sf[i] = SOC_time_morning[i][int(StartTime_secs.iloc[i][1])-1]
            
            SOC = SOC_sf
            v = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                     self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                     self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                     self.df_VehicleModels['Number_of_cells'][self.SubFleetId],SOC_sf,0,0)                      
            SOC_time, SOC_sf, power_ac_demanded_dis =\
                self.discharge_baseline(StartTime_secs, EndTime_secs, Miles,
                                        Purpose, MilesSubfleet, SOC, SOC_sf,
                                        sim_time, power_ac, v) 
                
            for i in range(self.N_SubFleets):    
                SOC_time[i][0:int(StartTime_secs.iloc[i][1])] = SOC_time_morning[i][0:int(StartTime_secs.iloc[i][1])]
            
            power_ac_demanded = power_ac_demanded_dis + power_ac_demanded
            
            # CHARGING STRATEGY   
            time_arrival_home = np.max(EndTime_secs, axis = 1)
            SOC_arrival_home = SOC_sf          
            for i in range(self.N_SubFleets):
                power_dc_arr[i] = self.power_dc_charger(self.df_VehicleModels['AC_Watts_Losses_0'][self.SubFleetId[i]],
                                                 self.df_VehicleModels['AC_Watts_Losses_1'][self.SubFleetId[i]],
                                                 self.df_VehicleModels['AC_Watts_Losses_2'][self.SubFleetId[i]],
                                                 self.df_VehicleModels['Max_Charger_AC_Watts'][self.SubFleetId[i]],
                                                 power_ac.iloc[i])
            v_oc = self.voltage_battery(self.df_VehicleModels['V_SOC_0'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_1'][self.SubFleetId],
                                        self.df_VehicleModels['V_SOC_2'][self.SubFleetId], 
                                        self.df_VehicleModels['Number_of_cells'][self.SubFleetId], SOC_arrival_home, 0, 0)       
            r_batt = self.resistance_battery(self.df_VehicleModels['R_SOC_0'][self.SubFleetId],
                                             self.df_VehicleModels['R_SOC_1'][self.SubFleetId],
                                             self.df_VehicleModels['R_SOC_2'][self.SubFleetId], SOC_arrival_home)            
            i_batt = self.current_charging(v_oc,r_batt,power_dc_arr)
            Ah_rate = i_batt/3600
            charging_rate = Ah_rate/self.df_VehicleModels['Ah_usable'][self.SubFleetId]
            # Variation of SOC that must be achieved
            delta_SOC = 1 - SOC_arrival_home
            
            # One hour before the TCIN all the subfleets must be fully charged
            StartTime_secs, EndTime_secs, Miles, Purpose, MilesSubfleet = self.match_schedule(day+1,SOC,v)
            time_full_charge = 24*3600 + StartTime_secs.iloc[:][1] - hours_before*3600
            time_start_charging = np.zeros([self.N_SubFleets,], dtype = int)
            for i in range(self.N_SubFleets):
                time_start_charging[i] = int(time_full_charge.iloc[i] - (delta_SOC[i]/charging_rate.iloc[i]))
                t2 = sim_time - time_start_charging[i]
                if t2 > 0:
                    SOC_time[i][int(time_arrival_home.iloc[i]):time_start_charging[i]] = SOC_arrival_home[i]
                    SOC_time[i][time_start_charging[i]:sim_time] = np.linspace(SOC_arrival_home[i],
                            SOC_arrival_home[i] + t2*charging_rate.iloc[i], t2)
                else:
                    SOC_time[i][int(time_arrival_home.iloc[i]):sim_time] = SOC_arrival_home[i]
                    
                # Power demanded to the grid
                if time_start_charging[i] < 24*3600:
                    power_ac_demanded[i][time_start_charging[i]:sim_time] =\
                        power_ac.iloc[i]*self.VehiclesSubFleet*(1 - 0.01*self.df_VehicleModels['Sitting_cars_per'][self.SubFleetId[i]])
                    time_charge_morning[i] = 0
                else:
                    power_ac_demanded[i][time_start_charging[i]:sim_time] = 0
                    time_charge_morning[i] = int(time_start_charging[i] - 24*3600)
        
            SOC = SOC_time[:,-1]
            SOC_sf = SOC
            
            # Eliminate burn-in day: tcin strategy requires this
            if day != 0:
                baseline_power = baseline_power + power_ac_demanded.sum(axis = 0)
                baseline_soc = baseline_soc + SOC_time.mean(axis = 0)
                baseline_std_soc = baseline_std_soc + SOC_time.std(axis = 0)

        return baseline_soc/(n_days_base), baseline_power/(n_days_base), baseline_std_soc/(n_days_base)
    
    def output_impact_metrics(self): 
        """
        This function exports the impact metrics of each sub fleet
        """
        impact_metrics_DATA = [["Impact Metrics File"],
                                ["state-of-health", "initial value", "final value", "degradation cost"]]
        for subfleet in range(self.N_SubFleets):
            impact_metrics_DATA.append(["battery-"+str(subfleet),
                                        str(self.soh_init[subfleet]),
                                        str(self.soh[subfleet]),
                                        str((self.soh_init[subfleet]-self.soh[subfleet])*self.eol_cost/100)])

        total_cost = sum((self.soh_init-self.soh)*self.eol_cost/100)
        impact_metrics_DATA.append(["Total degradation cost:", str(total_cost)])

        with open('impact_metrics.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(impact_metrics_DATA)     

        pass
    
    def change_config(self, fleet_config):
        """
        This function updates the fleet configuration settings programatically.
        :param fleet_config: an instance of FleetConfig
        """

        # change config
        self.is_P_priority = fleet_config.is_P_priority
        self.is_autonomous = fleet_config.is_autonomous
        self.FW_Param = fleet_config.FW_Param # FW_Param=[db_UF,db_OF,k_UF,k_OF]
        self.fw_function.db_UF = self.FW_Param[0]
        self.fw_function.db_OF = self.FW_Param[1]
        self.fw_function.k_UF  = self.FW_Param[2]
        self.fw_function.k_OF  = self.FW_Param[3]
        self.autonomous_threshold = fleet_config.autonomous_threshold
        self.Vset = fleet_config.v_thresholds
        
        pass