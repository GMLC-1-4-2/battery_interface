# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 13:46:46 2019
Description: 
Last update: 
Version: 1.0
Author: Jeff Maguire (NREL)
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
        
        df['MaxAnnualConditions'] = self.config_file.get('Water Heater Models', 'MaxAnnualConditions', fallback = None).split(',')
        #df['TtankInitial'] = self.config_file.get('Water Heater Models', 'TtankInitial', fallback = None).split(',')
        #df['TsetInitial'] = list(map(float, self.config_file.get('Water Heater Models', 'TsetInitial', fallback = None).split(',')))
        #df['Capacity'] = list(map(int, self.config_file.get('Water Heater Models', 'Capacity', fallback = None).split(',')))    
        #df['Type'] = list(map(float, self.config_file.get('Water Heater Models', 'Type', fallback = None).split(',')))    
        #df['Location'] = list(map(float, self.config_file.get('Water Heater Models', 'Location', fallback = None).split(','))) 
        #df['MaxServiceCalls'] = list(map(float, self.config_file.get('Water Heater Models', 'MaxServiceCalls', fallback = None).split(',')))

        return df

    def get_n_subfleets(self):
        return int(self.config_file.get('Water Heater Fleet', 'NumberSubfleets', fallback = 100))

    def get_run_baseline(self):
        return self.str_to_bool(self.config_file.get('Water Heater Fleet', 'RunBaseline', fallback = False))
    
    def get_n_days_MC(self):
        return int(self.config_file.get('Water Heater Fleet', 'NumberDaysBase', fallback = 10))
    
    def get_fleet_config(self):
        is_p_priority = self.str_to_bool(self.config_file.get('Fleet Configuration', 'Is_P_Priority', fallback = True))
        is_aut = self.str_to_bool(self.config_file.get('Fleet Configuration', 'IsAutonomous', fallback = False))
        return [is_p_priority, is_aut]
    
    def get_FW(self):
        fw_enabled = list()
        
        fw_enabled.append(self.str_to_bool(self.config_file.get('FW', 'FW21_Enabled', fallback = True)))
        # Discrete version of the response to frequency deviations (artificial inertia service)
        fw_enabled.append(list(map(float, (self.config_file.get('FW', 'db_UF', fallback = None).split(',')))))
        fw_enabled.append(list(map(float, (self.config_file.get('FW', 'db_OF', fallback = None).split(',')))))
        
        # TODO: These parameters must be removed in future realeases of the API
        fw_enabled.append(float(self.config_file.get('FW', 'k_UF', fallback = 0.05)))
        fw_enabled.append(float(self.config_file.get('FW', 'k_UF', fallback = 0.05)))
        fw_enabled.append(float(self.config_file.get('FW', 'P_avl', fallback = 1.0)))
        fw_enabled.append(float(self.config_file.get('FW', 'P_min', fallback = 0.0)))
        fw_enabled.append(float(self.config_file.get('FW', 'P_pre', fallback = 1.0)))
        
        return fw_enabled
    
    def get_impact_metrics_params(self):
        metrics = list()

        # Aveage tank baseline
        metrics.append(float(self.config_file.get('Impact Metrics', 'ave_Tin_base', fallback = 123)))
        # Aveage tank temperature under grid service
        metrics.append(float(self.config_file.get('Impact Metrics', 'ave_Tin_grid', fallback = 123)))
        # Cylces in baseline
        metrics.append(float(self.config_file.get('Impact Metrics', 'cycle_basee', fallback = 100)))
        # Cylces in grid operation
        metrics.append(float(self.config_file.get('Impact Metrics', 'cycle_grid', fallback = 100)))
        # State of Charge of the battery equivalent model under baseline
        metrics.append(float(self.config_file.get('Impact Metrics', 'SOCb_metric', fallback = 100)))
        # State of Charge of the battery equivalent model
        metrics.append(float(self.config_file.get('Impact Metrics', 'SOC_metric', fallback = 1.0)))
        # Unmet hours of the fleet
        metrics.append(float(self.config_file.get('Impact Metrics', 'unmet_hours', fallback = 1.0)))

        return metrics
        
    def get_service_weight(self):
        return float(self.config_file.get('Service Weighting Factor', 'ServiceWeight', fallback=0.5))