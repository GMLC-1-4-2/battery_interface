# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov, smshafiul.alam@inl.gov
Description: This class implements the Electrolyzer FleetInterface to integrate with a fleet of
Electrolyzers
"""

import sys
from os.path import dirname, abspath, join
from datetime import datetime
from warnings import simplefilter, filterwarnings, warn
import configparser
from numpy import polyfit, RankWarning, trapz, log10, exp, ndarray
from scipy.optimize import fsolve
from pandas import read_csv
from matplotlib.pyplot import figure, subplot2grid
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from fleet_interface import FleetInterface
from fleet_response import FleetResponse
from csv import writer
from grid_info_artificial_inertia import GridInfo
simplefilter('ignore', RankWarning)
filterwarnings("ignore", category=RuntimeWarning)
if sys.version_info >= (3,6,7):
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
    

class ElectrolyzerFleet(FleetInterface):
    """
    Electrolyzer Fleet Class
    """

    def __init__(self, grid_info, mdl_config="config.ini", mdl_type="Electrolyzer", **kwargs):
        """
        :param GridInfo: GridInfo object derived from the GridInfo Class
        :param mdl_config: File location for config.ini
        :param mdl_config: Model parameters to be loaded from config.ini
        :param kwargs:
        """

        # Load the config file that has model parameters
        self.base_path = dirname(abspath(__file__))
        self.config = configparser.ConfigParser()
        self.config.read(join(self.base_path, mdl_config))

        # Read the model parameters from config file with defaults as fallback
        self.ey_model_name = self.config.get(mdl_type, "Name", fallback="Default Electrolyzer Fleet")
        self.ey_T = float(self.config.get(mdl_type, "T", fallback=25))
        self.ey_Pe = float(self.config.get(mdl_type, "Pe", fallback=101000))
        self.ey_Pe_out = float(self.config.get(mdl_type, "Pe_out", fallback=50000000))
        self.ey_E_size = float(self.config.get(mdl_type, "E_size", fallback=2.0))
        self.ey_eta_c = float(self.config.get(mdl_type, "eta_c", fallback=0.8))
        self.ey_A = float(self.config.get(mdl_type, "A", fallback=0.25))
        self.ey_Nc = float(self.config.get(mdl_type, "Nc", fallback=12))
        self.ey_F = float(self.config.get(mdl_type, "F", fallback=96485.34))
        self.ey_ne0 = float(self.config.get(mdl_type, "ne0", fallback=2))
        self.ey_charge_lvl_init = float(self.config.get(mdl_type, "charge_lvl_init", fallback=10))
        self.ey_DG_25 = float(self.config.get(mdl_type, "DG_25", fallback=237000.0))
        self.ey_DG_80 = float(self.config.get(mdl_type, "DG_80", fallback=228480.0))
        self.ey_DH = float(self.config.get(mdl_type, "DH", fallback=286000.0))
        self.ey_R = float(self.config.get(mdl_type, "R", fallback=8.31445))
        self.ey_Ne = float(self.config.get(mdl_type, "Ne", fallback=50))
        self.ey_V_tank = float(self.config.get(mdl_type, "V_tank", fallback=0.3))
        self.ey_Nt = float(self.config.get(mdl_type, "Nt", fallback=3))
        self.ey_r1 = float(self.config.get(mdl_type, "r1", fallback=7.331e-5))
        self.ey_r2 = float(self.config.get(mdl_type, "r2", fallback=-1.107e-7))
        self.ey_r3 = float(self.config.get(mdl_type, "r3", fallback=0.0))
        self.ey_s1 = float(self.config.get(mdl_type, "s1", fallback=1.586e-1))
        self.ey_s2 = float(self.config.get(mdl_type, "s2", fallback=1.378e-3))
        self.ey_s3 = float(self.config.get(mdl_type, "s3", fallback=-1.606e-5))
        self.ey_t1 = float(self.config.get(mdl_type, "t1", fallback=1.599e-2))
        self.ey_t2 = float(self.config.get(mdl_type, "t2", fallback=-1.302))
        self.ey_t3 = float(self.config.get(mdl_type, "t3", fallback=4.213e2))
        self.ey_I_initial = int(self.config.get(mdl_type, "I_initial", fallback=0))
        self.ey_I_final = int(self.config.get(mdl_type, "I_final", fallback=870))
        self.ey_I_step = int(self.config.get(mdl_type, "I_step", fallback=1))
        self.ey_a1 = float(self.config.get(mdl_type, "a1", fallback=0.995))
        self.ey_a2 = float(self.config.get(mdl_type, "a2", fallback=-9.5788))
        self.ey_a3 = float(self.config.get(mdl_type, "a3", fallback=-0.0555))
        self.ey_a4 = float(self.config.get(mdl_type, "a4", fallback=0.0))
        self.ey_a5 = float(self.config.get(mdl_type, "a5", fallback=1502.7083))
        self.ey_a6 = float(self.config.get(mdl_type, "a6", fallback=-70.8005))
        self.ey_a7 = float(self.config.get(mdl_type, "a7", fallback=0.0))
        self.ey_gamma = float(self.config.get(mdl_type, "gamma", fallback=1.41))
        self.ey_cpH2 = float(self.config.get(mdl_type, "cpH2", fallback=14.31))
        self.ey_x01 = float(self.config.get(mdl_type, "x0_1", fallback=1.6))
        self.ey_x02 = float(self.config.get(mdl_type, "x0_2", fallback=80))
        self.ey_Pmin_fleet = float(self.config.get(mdl_type, "Pmin_fleet", fallback=30))
        self.ey_Pmax_fleet = float(self.config.get(mdl_type, "Pmax_fleet", fallback=130))
        self.ey_At = float(self.config.get(mdl_type, "At", fallback=47))
        self.ey_len = float(self.config.get(mdl_type, "len", fallback=2.54))
        self.ey_Phi_0 = float(self.config.get(mdl_type, "Phi_0", fallback=5.9e-5))
        self.ey_E_phi = float(self.config.get(mdl_type, "E_phi", fallback=42.7))
        self.ey_b = float(self.config.get(mdl_type, "b", fallback=1.55e-5))
        self.ey_LHV_H2 = float(self.config.get(mdl_type, "LHV_H2", fallback=120000))
        self.ey_ser_wght = float(self.config.get(mdl_type, "service_weight", fallback=1.0))
        self.is_P_priority = self.bool_check(self.config.get(mdl_type, "is_P_priority", fallback=True))
        self.FW21_Enabled = self.bool_check(self.config.get(mdl_type, "FW21_Enabled", fallback=False))
        self.is_autonomous = self.bool_check(self.config.get(mdl_type, "is_autonomous", fallback=False))
        self.ey_db_UF = float(self.config.get(mdl_type, "db_UF", fallback=0.36))
        self.ey_db_OF = float(self.config.get(mdl_type, "db_OF", fallback=0.36))
        self.ey_k_UF = float(self.config.get(mdl_type, "k_UF", fallback=0.05))
        self.ey_k_OF = float(self.config.get(mdl_type, "k_OF", fallback=0.05))
        self.__P_pre = float(self.config.get(mdl_type, "P_pre", fallback=-1.0))

        # Establish the location that the Electrolyzer fleet is connected in the grid
        if isinstance(grid_info, GridInfo):
            self.grid = grid_info
        else:
            # Set services to false if GridInfo is not called correctly during fleet init.
            self.is_P_priority = True
            self.is_autonomous = False
            self.FW21_Enabled = False
            warn("GridInfo() needs to be loaded with AI data. "
                 "Please check your Electrolyzer fleet initialization code!! "
                 "Fleet services will be set to False")

        # Pre-load a base profile for the Electrolyer based on price-demand response curve
        self.ey_pbase = join(self.base_path, self.config.get(mdl_type, "power_data", fallback="Pbase.txt"))

        if self.config.sections()[0] != mdl_type:
            print("Error reading config.ini file for model:"+"\t"*3+"%s [FAIL]!!" % mdl_type)
            print("Model found in config.ini file:"+"\t"*5+"%s!!\n"
                  "Default modelling parameters will be used!!\n" % self.config.sections()[0])
        else:
            print("Model parameters found for:"+"\t"*5+"%s [OKAY]\n" % self.config.sections()[0])

        # Initialize state parameters for the Electrolyzer fleet model
        self.f = None
        self.__V = self.__Ir = self.__V_age = self.__Ir_age = self.__p_base = 0.0
        self.__nf = self.__nf_age = self.__ne = self.__ne_age = 0.0
        self.__Tout = self.__W_c = self.__p_tot = self.__pe_out = 0.0
        self.__Qh2_V = self.__Qh2_m = self.__Qh2_m_age = 0.0
        self.__m_dotH2 = self.__m_dotH2_age = 0.0
        self.lka_h2 = self.__Phi = self.__dmdot_dt = 0.0
        self.__eta_ch = self.__Qh2_out = 0.0
        self.__inc = 0

        # THIS NEEDS TO BE MODFIED BASED ON FLEET P OUTPUT
        self.fleet_rating = self.ey_Ne*self.ey_E_size

        # Set the operating range for the Electrolyzer fleet: PminkW <= P_opt <= PmaxkW
        self.P_opt = lambda p_req, p_min, p_max: max(p_min, min(p_max, p_req))
        self.DG = self.ey_DG_25-(self.ey_T-25)/55*(self.ey_DG_25-self.ey_DG_80)
        self.V_rev = self.DG/self.ey_ne0/self.ey_F
        self.V_init = round(self.V_rev, 2)

        # Thermo-neutral voltage
        self.Vtn = self.ey_DH/self.ey_ne0/self.ey_F

        # Max. state of charge in the hydrogen tank
        self.max_charge = self.ey_Pe_out

        # Initial state of charge (pressure) in the tank
        self.P_tank = self.ey_charge_lvl_init*1e-2*self.ey_Pe_out

        # SOC initial
        self.soc = self.soc_age = self.P_tank/self.max_charge

        # Initial number of H2 moles in the tank
        self.ni = self.P_tank*self.ey_V_tank/self.ey_R/(self.ey_T+273.15)

        # initial moles w/o and w/ ageing
        self.moles = self.moles_age = self.ni*self.ey_Nt

        # Leakage variables
        self.ey_At *= self.ey_Nt
        self.ey_len /= 1e3

        # Fit the base power profile for Electrolyzer
        self.p = self.fit_pdat(self.ey_pbase, 5*60)

        # Output metrics dataframe -- TO BE CHANGED TO PANDAS DF
        self.metrics = [['ts', 'V_ideal', 'V_age', 'ne_ideal', 'ne_age', 'Soc_ideal', 'Soc_age',
                         'Lka_H2', 'nch', 'P_togrid', 'P_service', 'f']]

    def process_request(self, fleet_request):
        resp = self.run_ey_fleet(fleet_request.ts_req, fleet_request.sim_step,
                                 fleet_request.P_req, False, fleet_request.start_time)
        return resp

    def forecast(self, requests):
        soc_state, soc_state_age, state = self.soc, self.soc_age, self.__inc
        resp = [self.run_ey_fleet(req.ts_req, req.sim_step, req.P_req, True, req.start_time) for req in requests]
        self.soc, self.soc_age, self.__inc = soc_state, soc_state_age, state
        return resp

    def run_ey_fleet(self, ts, sim_step, Preq, forecast=False, start_time=None):
        """
        :param ts: Request created for current time-step: datetime
        :param sim_step: Request for simulation time-step: timedelta object
        :param Preq: Request for current real power request
        :param forecast: Returns fleet response forcast
        :param start_time: Request for current real power request
        :return resp: Fleet response object
        """
        if self.P_tank >= self.max_charge:
            self.lka_h2 = self.lka_h2/2*1
        else:
            # Create base power profile
            if isinstance(self.p, ndarray):
                self.__p_base = sum([self.p[j]*(self.__inc+1)**(21-j) for j in range(22)])
            else:
                self.__p_base = self.p
            # Ptogrid: -Pbase for None or zero requests since Ey is a load
            if Preq is None or float(Preq) == 0.0:
                Preq = self.__p_base
            # Ptogrid: Preq-Pbase for +ve or -ve requests
            else:
                Preq -= self.__p_base
            # Compute the power consumed by the fleet
            self.__ey_p_calc(Preq)

            if self.FW21_Enabled and self.is_autonomous:
                # all in kW
                Preq, self.f = self.frequency_watt(p_pre=self.__pe_out*1e-3, p_avl=self.ey_Pmax_fleet,
                                                   p_min=self.ey_Pmin_fleet,
                                                   ts=ts, start_time=start_time)
                self.__pe_out = Preq*1e3

            # Update SOC
            self.__soc_calc()
        self.__inc += 1

        # Responses
        resp = FleetResponse()
        resp.ts = ts
        resp.sim_step = sim_step
        resp.C = 0
        resp.dT_hold_limit = 0
        resp.E = self.soc
        resp.Eff_charge = self.__eta_ch
        resp.Eff_discharge = 1.0
        resp.P_dot_down = 0
        resp.P_dot_up = 0
        resp.P_togrid = -self.__pe_out * 1e-3  # (kW)
        resp.P_togrid_max = -self.ey_Pmax_fleet
        resp.P_togrid_min = -self.ey_Pmin_fleet
        resp.P_service = resp.P_togrid+self.__p_base  # (kW)
        resp.P_service_max = self.ey_Pmax_fleet-self.__p_base
        resp.P_service_min = self.__p_base-self.ey_Pmin_fleet
        resp.Q_dot_down = 0
        resp.Q_dot_up = 0
        resp.Q_service = 0
        resp.Q_service_max = 0
        resp.Q_service_min = 0
        resp.Q_togrid = 0
        resp.Q_togrid_max = 0
        resp.Q_togrid_min = 0
        resp.T_restore = 0
        resp.P_base = -self.__p_base    # (kW)
        resp.Q_base = 0
        resp.Strike_price = 0
        resp.SOC_cost = 0
        resp.dmdot = self.__dmdot_dt
        resp.moles = self.moles
        resp.P_tank = self.P_tank

        # Impact metrics
        if not forecast:
            self.metrics.append([str(ts), str(self.__V), str(self.__V_age), str(self.__ne),
                                 str(self.__ne_age), str(resp.E), str(self.soc_age*1e2),
                                 str(self.lka_h2), str(resp.Eff_charge), str(resp.P_togrid),
                                 str(resp.P_service), str(self.f)])

        # Print SoC status every 5 secs.
        if self.__inc % 5000 == 0:
            print("Soc:%4.2f%%" % (resp.E*1e2))

        return resp

    @staticmethod
    def __vi_calc(x, Pri, Nc, V_rev, T, r1, r2, s1, s2, s3, t1, t2, t3, A):
        fa = list([x[0] - V_rev - (r1 + r2 * T) * x[1] / A - (s1 + s2 * T + s3 * T ** 2) * log10(
            (t1 + t2 / T + t3 / T ** 2) * x[1] / A + 1)])
        fa.append((Nc * x[0]) * x[1] - Pri)
        return fa

    def __ey_p_calc(self, p_req):
        # Check for operating range of the fleet

        Preq = float(self.P_opt(abs(p_req), self.ey_Pmin_fleet, self.ey_Pmax_fleet))

        Pr = abs(Preq) * 1e3 / self.ey_Ne  # Watts

        # Compute voltage and current for 1 Electrolyzer stack
        self.__V, self.__Ir = fsolve(self.__vi_calc, [self.ey_x01, self.ey_x02],
                                     args=(Pr, self.ey_Nc, self.V_rev, self.ey_T,
                                           self.ey_r1, self.ey_r2, self.ey_s1, self.ey_s2,
                                           self.ey_s3, self.ey_t1, self.ey_t2, self.ey_t3,
                                           self.ey_A))

        # Total power for the Ne number of Electrolyzers or fleet
        self.__pe_out = self.ey_Ne * self.ey_Nc * self.__V * self.__Ir

        # Ageing
        self.__V_age = self.__V + ((self.__inc + 1) * 3.88888888888887e-08)
        self.__Ir_age = self.__p_base / (self.__V_age * self.ey_Nc)

        # Compute Faraday Efficiency
        self.__nf = self.ey_a1 * exp((self.ey_a2 + self.ey_a3 * self.ey_T + self.ey_a4 * self.ey_T ** 2) /
                                     (self.__Ir / self.ey_A) + (self.ey_a5 + self.ey_a6 * self.ey_T + self.ey_a7 * self.ey_T ** 2) /
                                     (self.__Ir / self.ey_A) ** 2)
        self.__nf_age = self.ey_a1 * exp((self.ey_a2 + self.ey_a3 * self.ey_T + self.ey_a4 * self.ey_T ** 2) /
                                         (self.__Ir_age / self.ey_A) + (self.ey_a5 + self.ey_a6 * self.ey_T + self.ey_a7 * self.ey_T ** 2) /
                                         (self.__Ir_age / self.ey_A) ** 2)

        # Energy (or voltaje) efficiency of a cell
        self.__ne = self.Vtn / self.__V
        self.__ne_age = self.Vtn / self.__V_age

        # Flow of H2 produced
        self.__Qh2_V = 80.69 * self.ey_Nc * self.__Ir * self.__nf / 2 / self.ey_F  # (Nm^3/h)
        self.__Qh2_m = self.ey_Ne * self.ey_Nc * self.__Ir * self.__nf / 2 / self.ey_F  # (mol/s)
        self.__Qh2_m_age = self.ey_Ne * self.ey_Nc * self.__Ir_age * self.__ne_age / 2 / self.ey_F  # (mol/s)
        self.__m_dotH2 = self.__Qh2_m * 2 * 1e-3  # 1mol = 2grams (kg/s)
        self.__m_dotH2_age = self.__Qh2_m_age * 2 * 1e-3  # 1mol = 2grams (kg/s)

        # Compressor model
        self.P_tank = self.moles / self.ey_Nt * self.ey_R * (self.ey_T + 273.15) / self.ey_V_tank
        self.__Tout = (self.ey_T + 273.15) * (self.P_tank / self.ey_Pe) ** ((self.ey_gamma - 1) / self.ey_gamma)
        self.__W_c = (self.__m_dotH2 / self.ey_eta_c) * self.ey_cpH2 * (self.__Tout - (self.ey_T + 273.15))  # (kW)

        # Total power demanded from the grid in Watts
        self.__p_tot = self.__W_c * 1e3 + self.__pe_out

    def __soc_calc(self):
        # Storage Tank

        # Compute hydrogen leakage from tank
        self.__Phi = self.ey_Phi_0 * exp(
            -self.ey_E_phi / (self.ey_R * 1e-3) / (self.ey_T + 273.15))  # (mol s^-1 m^-1 MPa^-0.5)
        
        # fugacity
        f = self.P_tank * 1e-6 * exp(self.P_tank * 1e-6 * self.ey_b / (self.ey_R * 1e-3) / (self.ey_T + 273.15))
        J = self.__Phi / self.ey_len * 2 * f ** 0.5  # (g m^-2 s^-1)

        # total hydrogen lost in time t (g)
        self.lka_h2 += J * self.ey_At * 1
        self.__dmdot_dt = self.__Qh2_m - self.__Qh2_out
        
        # Number of moles in at given instant in the system of tanks
        self.moles += self.__dmdot_dt*1
        
        # Number of moles in at given instant in the system of tanks w/ aging and leakage
        self.moles_age += self.__Qh2_m_age * 1 - self.lka_h2 / 2 * 1

        # Charging efficiency
        self.__eta_ch = self.ey_LHV_H2 * self.__m_dotH2 * 1e3 / self.__p_tot  # (W/W)
        self.soc = round(self.P_tank / self.max_charge, 3)
        self.soc_age = round(
            self.moles_age / self.ey_Nt * self.ey_R * (self.ey_T + 273.15) / self.ey_V_tank / self.max_charge, 3)
        if self.soc > 1.0 or self.soc < 0.0:
            sys.exit(print("SOC limit violation!!" + "\t" * 6 + " [!!]\n"))

    @staticmethod
    def bool_check(b_in):
        if str(b_in) in ('TRUE', 'True', 'T', 't', 'Yes', 'YES', 'y', 'yes'):
            return True
        elif str(b_in) in ('FALSE', 'False', 'F', 'f', 'No', 'NO', 'n', 'no'):
            return False
        else:
            return ValueError('%s is not Boolean. Please set True/False in config.ini' % b_in)

    def output_metrics2(self, filename):
        base_path = dirname(abspath(__file__))
        self.__metrics.to_csv(join(base_path, str(filename)+'.csv'), sep=',', encoding='utf-8')
        print("Impact metrics file has been created" + "\t" * 5 + " [OKAY]\n")

    def output_metrics(self, filename):
        base_path = dirname(abspath(__file__))
        with open(join(base_path, str(filename)+'.csv'), 'w', newline='') as out:
            write = writer(out)
            write.writerows(self.metrics)
            print("Impact metrics file has been created"+"\t"*5+" [OKAY]\n")

    def frequency_watt(self, p_pre=1.0, p_avl=1.0, p_min=0.1, ts=datetime.utcnow(), location=0, start_time=None):
        f = self.grid.get_frequency(ts, location, start_time)
        P_pre = -p_pre / self.ey_Pmax_fleet
        P_avl = -p_avl / self.ey_Pmax_fleet
        P_min = -p_min / self.ey_Pmax_fleet
        if f < 60 - self.ey_db_UF:
            p_set = min(P_min, P_pre + (60 - self.ey_db_UF - f) / (60 * self.ey_k_UF))
        elif f > 60 + self.ey_db_OF:
            p_set = max(P_avl, P_pre + (60 + self.ey_db_OF - f) / (60 * self.ey_k_OF))
        else:
            p_set = P_pre
        p_set *= -self.ey_Pmax_fleet
        return p_set, f

    def assigned_service_kW(self):
        return self.ey_ser_wght*self.fleet_rating

    @staticmethod
    def ne_calc(filename, e_size, ne=None):
        """
        :param filename: Time-stamped power curve input data as CSV
        :param e_size: Size of a single Electrolyzer in kW
        :param ne: User input for number of Electrolyzers
        :return: Optimum number of Electrolyzers
        """
        df = read_csv(filename, header=None, parse_dates=[0], names=['datetime', 'Pval'])
        opt_ne = int(round(trapz(df['Pval']) / len(df) / e_size))
        if int(ne) != opt_ne:
            print("Number of Electrolyzers does not fit the power curve:\t\t[%d]" % int(ne))
            print("Optimum Electrolyzers used for this simulation run:\t\t[%d]" % opt_ne)
            return opt_ne
        return ne

    def fit_pdat(self, filename, time_interval=None):
        """
        Read demand profile and check if timestamp interval is at least in seconds.
        Execute only if freq does not match: milli, micro, or nano
        :param filename: Time-stamped power curve input data as CSV
        :param time_interval: Specify the data time interval in seconds
        :return p: Curve-fit results using Least square curve-fitting method or computed Pbase value
        """
        p_val = None
        if time_interval is None:
            try:
                df = read_csv(filename, header=None, parse_dates=[0], index_col=0, nrows=10)
                interval = df.index.inferred_freq
            except (AttributeError, TypeError):
                raise Exception("\tUnable to infer time interval from input data\n"
                                "\tPlease specify the time_interval parameter in seconds!!\n")
            if any(i in interval for i in ('L', 'ms', 'U', 'us', 'N')) is False:
                print("Power data time-interval is at least in seconds:\t\t[OKAY]")
                df = read_csv(filename, header=None, parse_dates=[0], names=['datetime', 'Pval'])
                df['sec'] = df['datetime'].sub(df['datetime'].iloc[0]).dt.total_seconds()
            else:
                raise Exception("\tTime-series data should be at least in seconds\n"
                                "\te.g.:\n"
                                "\t\t2019-01-21 00:00:00  646.969697\n"
                                "\t\t2019-01-21 00:05:00  642.818182\n"
                                "\t\t...................  ..........\n"
                                "\t\tYYYY-MM-DD HH:MM:SS  Value\n")
        else:
            try:
                df = read_csv(filename, header=None, names=['Pval'])
                df['sec'] = [i for i in range(0, len(df) * time_interval, time_interval)]
                # Least-square curve-fitting
                p_val = polyfit(df['sec'].values, df['Pval'].values, 21)
            except FileNotFoundError:
                # Set Pbase as an average of Pmin and Pmax operating range of a single Electrolyzer fleet
                p_val = sum([self.ey_Pmax_fleet + self.ey_Pmin_fleet]) / 2.0
                warn("File not found. Please ensure path or file name is correct for power_data in config.ini!!")
                print("Pbase is set as a constant to %4.2fkW" % p_val)
        return p_val

    @staticmethod
    def static_plots(**kwargs):
        base_path = dirname(abspath(__file__))
        plots = int(len(kwargs))
        nplots = int(2*plots)
        fig1 = figure(figsize=(20, 12))
        fig1.subplots_adjust(wspace=0.9)
        fig1.subplots_adjust(hspace=9.5)
        res_plt = {}
        for i, (k, v) in enumerate(kwargs.items()):
            if i % 2 == 0:
                res_plt[str(i)] = subplot2grid((nplots, plots), (i, 0), rowspan=2, colspan=3)
            else:
                res_plt[str(i)] = subplot2grid((nplots, plots), (i-1, 3), rowspan=2, colspan=3)

            res_plt[str(i)].set_title(k)
            res_plt[str(i)].plot(v[0], '-.r')
            res_plt[str(i)].set_ylabel(v[1])
            res_plt[str(i)].grid()
        fig1.savefig(join(base_path, "Ey_result_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                     bbox_inches='tight')
