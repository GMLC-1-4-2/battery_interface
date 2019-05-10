# -*- coding: utf-8 -*-
"""
Created on Tue Mar 18 2019
Description: 
Last update: 
Version: 1.0
@author: Jin Dong (ORNL)
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
        
        df['Total_HVACs'] = self.config_file.get('HVACs', 'NumberFleets', fallback = None).split(',')
        df['Max_AC_Watts'] = self.config_file.get('HVACs', 'Max_AC_Watts', fallback = None).split(',')

        return df

    # def get_n_subfleets(self):
    #     return int(self.config_file.get('Electric Vehicles', 'NumberSubfleets', fallback = 100))

    def get_run_baseline(self):
        return self.str_to_bool(self.config_file.get('HVACs', 'RunBaseline', fallback = False))
    
  
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
        
        metrics.append(float(self.config_file.get('Impact Metrics', 'ave_Tin', fallback = 23)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'ave_TinB', fallback = 23)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'CycleBase', fallback = 10)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'CycleGrid', fallback = 10)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'SOCb_metric', fallback = 0.6)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'SOC_metric', fallback = 0.6)))
        metrics.append(float(self.config_file.get('Impact Metrics', 'UnmetHours', fallback = 0)))
        
        # metrics.append(float(self.config_file.get('Impact Metrics', 'EnergyEfficiency', fallback = 1.0)))
        
        return metrics
        
    def get_service_weight(self):
        return float(self.config_file.get('Service Weighting Factor', 'ServiceWeight', fallback=1.0))