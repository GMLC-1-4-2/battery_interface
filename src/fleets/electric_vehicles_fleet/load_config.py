# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 13:46:46 2019

Description: 

Last update: 
Version: 1.0
Author: afernandezcanosa@anl.gov
"""

import pandas as pd


class LoadConfig(object):
    
    def __init__(self, config_file):
        self.config_file = config_file
        
    def str_to_bool(self, s):
        if s == 'True':
            return True
        elif s == 'False':
            return False
        else:
            raise ValueError('Insert boolean values in the config file')
        
    def get_config_models(self):
        df = pd.DataFrame()
        
        df['Vehicle_id'] = self.config_file.get('Vehicle Models', 'VehicleId', fallback = None).split(',')
        df['Model'] = self.config_file.get('Vehicle Models', 'Model', fallback = None).split(',')
        df['Wh_mi'] = list(map(float, self.config_file.get('Vehicle Models', 'WhMi', fallback = None).split(',')))
        df['Number_of_cells'] = list(map(int, self.config_file.get('Vehicle Models', 'NumberCells', fallback = None).split(',')))    
        df['Ah_usable'] = list(map(float, self.config_file.get('Vehicle Models', 'AhNominal', fallback = None).split(',')))    
        df['V_SOC_0'] = list(map(float, self.config_file.get('Vehicle Models', 'V_Oc_SoC_0', fallback = None).split(','))) 
        df['V_SOC_1'] = list(map(float, self.config_file.get('Vehicle Models', 'V_Oc_SoC_1', fallback = None).split(',')))
        df['V_SOC_2'] = list(map(float, self.config_file.get('Vehicle Models', 'V_Oc_SoC_2', fallback = None).split(',')))
        df['R_SOC_0'] = list(map(float, self.config_file.get('Vehicle Models', 'R_SoC_0', fallback = None).split(','))) 
        df['R_SOC_1'] = list(map(float, self.config_file.get('Vehicle Models', 'R_SoC_1', fallback = None).split(',')))
        df['R_SOC_2'] = list(map(float, self.config_file.get('Vehicle Models', 'R_SoC_2', fallback = None).split(',')))
        df['AC_Watts_Losses_0'] = list(map(float, self.config_file.get('Vehicle Models', 'AC_Watts_Losses_0', fallback = None).split(',')))
        df['AC_Watts_Losses_1'] = list(map(float, self.config_file.get('Vehicle Models', 'AC_Watts_Losses_1', fallback = None).split(',')))
        df['AC_Watts_Losses_2'] = list(map(float, self.config_file.get('Vehicle Models', 'AC_Watts_Losses_2', fallback = None).split(',')))
        df['Max_Charger_AC_Watts'] = list(map(float, self.config_file.get('Vehicle Models', 'Max_Charger_AC_Watts', fallback = None).split(',')))
        df['Total_Vehicles'] = list(map(int, self.config_file.get('Vehicle Models', 'Total_Vehicles', fallback = None).split(',')))
        df['Sitting_cars_per'] = list(map(float, self.config_file.get('Vehicle Models', 'Sitting_Cars_Per', fallback = None).split(',')))
        
        return df

    def get_n_subfleets(self):
        return int(self.config_file.get('Electric Vehicles', 'NumberSubfleets', fallback = 100))

    def get_run_baseline(self):
        return self.str_to_bool(self.config_file.get('Electric Vehicles', 'RunBaseline', fallback = False))
    
    def get_n_days_MC(self):
        return int(self.config_file.get('Electric Vehicles', 'NumberDaysBase', fallback = 10))
            
    def get_weibull_exp(self):
        return float(self.config_file.get('Weibull Distribution', 'Exponent', fallback = 3))
    
    def get_weibull_peak(self):
        return 1./float(self.config_file.get('Weibull Distribution', 'InvPeak', fallback = 0.33))
            
    def get_charged_at_work_per(self):
        return 0.01*float(self.config_file.get('Statistical Values', 'ChargedAtWorkPer', fallback = 20))
    
    def get_charged_at_other_per(self):
        return 0.01*float(self.config_file.get('Statistical Values', 'ChargedAtOtherPer', fallback = 5))
    
    def get_charging_strategies(self):
        names = self.config_file.get('Statistical Values', 'ChargingStrategiesNames', fallback = None).split(',')
        perc  = list(map(float, self.config_file.get('Statistical Values', 'ChargingStrategiesPer', fallback = None).split(',')))
        return [names, perc]
    
    def get_fleet_config(self):
        is_p_priority = self.str_to_bool(self.config_file.get('Fleet Configuration', 'Is_P_Priority', fallback = True))
        is_aut = self.str_to_bool(self.config_file.get('Fleet Configuration', 'IsAutonomous', fallback = False))
        return [is_p_priority, is_aut]
    
    def get_FW(self):
        fw_enabled = list()
        
        fw_enabled.append(self.str_to_bool(self.config_file.get('FW', 'FW21_Enabled', fallback = True)))
        fw_enabled.append(float(self.config_file.get('FW', 'db_UF', fallback = 0.036)))
        fw_enabled.append(float(self.config_file.get('FW', 'db_OF', fallback = 0.036)))
        fw_enabled.append(float(self.config_file.get('FW', 'k_UF', fallback = 0.05)))
        fw_enabled.append(float(self.config_file.get('FW', 'k_UF', fallback = 0.05)))
        fw_enabled.append(float(self.config_file.get('FW', 'P_avl', fallback = 1.0)))
        fw_enabled.append(float(self.config_file.get('FW', 'P_min', fallback = 0.0)))
        fw_enabled.append(float(self.config_file.get('FW', 'P_pre', fallback = 1.0)))
        
        return fw_enabled
    
    def get_impact_metrics_params(self):
        metrics = list()
        
        metrics.append(float(self.config_file.get('Impact Metrics', 'EolCost', fallback = 1000)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'CycleLife', fallback = 1000)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'SohInit', fallback = 100)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'EnergyEfficiency', fallback = 1.0)))
        
        return metrics
        
        
        
