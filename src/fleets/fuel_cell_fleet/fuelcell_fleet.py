# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
Description: This class implements the FuelCell FleetInterface to integrate with a fleet of
FuelCells
"""

import sys
from os.path import dirname, abspath, join
from warnings import simplefilter, filterwarnings, warn
import configparser
from datetime import datetime
from numpy import polyfit, convolve, RankWarning, log, exp, ndarray
from pandas import read_csv
from scipy.optimize import fsolve
from matplotlib.pyplot import figure, subplot2grid
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from fleet_interface import FleetInterface
from fleet_response  import FleetResponse
from csv import writer
import csv
from grid_info_artificial_inertia import GridInfo
from utils import ensure_ddir
simplefilter('ignore', RankWarning)
filterwarnings("ignore", category=RuntimeWarning)
if sys.version_info >= (3,6,7):
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()


class FuelCellFleet(FleetInterface):
    """
    FuelCell Fleet Class
    """

    def __init__(self, grid_info, mdl_config="config.ini", mdl_type="FuelCell", **kwargs):
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
        self.fc_model_name = self.config.get(mdl_type, "Name", fallback="Default FuelCell Fleet")
        self.fc_T = float(self.config.get(mdl_type, "T", fallback=70))
        self.fc_Ts = float(self.config.get(mdl_type, "Ts", fallback=25))
        self.fc_Pe = float(self.config.get(mdl_type, "Pe", fallback=101000))
        self.fc_Pe_out = float(self.config.get(mdl_type, "Pe_out", fallback=50000000))
        self.fc_size = float(self.config.get(mdl_type, "Fc_size", fallback=1.6))
        self.fc_A = float(self.config.get(mdl_type, "A", fallback=200))
        self.fc_Nc = float(self.config.get(mdl_type, "Nc", fallback=20))
        self.fc_F = float(self.config.get(mdl_type, "F", fallback=96485.34))
        self.fc_ne0 = float(self.config.get(mdl_type, "ne0", fallback=2))
        self.fc_charge_lvl_min = float(self.config.get(mdl_type, "charge_lvl_min", fallback=19))
        self.fc_charge_lvl_max = float(self.config.get(mdl_type, "charge_lvl_max", fallback=95))
        self.fc_DG_25 = float(self.config.get(mdl_type, "DG_25", fallback=237100.0))
        self.fc_DG_200 = float(self.config.get(mdl_type, "DG_200", fallback=220370.0))
        self.fc_DH = float(self.config.get(mdl_type, "DH", fallback=286000.0))
        self.fc_R = float(self.config.get(mdl_type, "R", fallback=8.31447))
        self.fc_Nfc = float(self.config.get(mdl_type, "Nfc", fallback=50))
        self.fc_V_tank = float(self.config.get(mdl_type, "V_tank", fallback=0.3))
        self.fc_Nt = float(self.config.get(mdl_type, "Nt", fallback=8))
        self.fc_I_initial = int(self.config.get(mdl_type, "I_initial", fallback=0))
        self.fc_I_final = int(self.config.get(mdl_type, "I_final", fallback=200))
        self.fc_I_step = int(self.config.get(mdl_type, "I_step", fallback=1))
        self.fc_alpha = float(self.config.get(mdl_type, "alpha", fallback=0.5))
        self.fc_a = float(self.config.get(mdl_type, "a0", fallback=3e-5))
        self.fc_b = float(self.config.get(mdl_type, "b", fallback=8e-6))
        self.fc_i_n = float(self.config.get(mdl_type, "i_n", fallback=-0.002))
        self.fc_i_0 = float(self.config.get(mdl_type, "i_0", fallback=6.7e-5))
        self.fc_i_L = float(self.config.get(mdl_type, "i_L", fallback=0.9))
        self.fc_R_tot = float(self.config.get(mdl_type, "R_tot", fallback=-0.030))
        self.fc_Patm = float(self.config.get(mdl_type, "Patm", fallback=101000))
        self.fc_Tau_e = float(self.config.get(mdl_type, "Tau_e", fallback=80))
        self.fc_Lambda = float(self.config.get(mdl_type, "Lambda", fallback=0.00333))
        self.fc_pH2 = float(self.config.get(mdl_type, "pH2", fallback=0.5))
        self.fc_pO2 = float(self.config.get(mdl_type, "pO2", fallback=0.8))
        self.fc_x01 = float(self.config.get(mdl_type, "x0_1", fallback=0.7))
        self.fc_x02 = float(self.config.get(mdl_type, "x0_2", fallback=80))
        self.fc_Pmin_fleet = float(self.config.get(mdl_type, "Pmin_fleet", fallback=30))
        self.fc_Pmax_fleet = float(self.config.get(mdl_type, "Pmax_fleet", fallback=130))
        self.fc_At = float(self.config.get(mdl_type, "At", fallback=47))
        self.fc_len = float(self.config.get(mdl_type, "len", fallback=2.54))
        self.fc_Phi_0 = float(self.config.get(mdl_type, "Phi_0", fallback=5.9e-5))
        self.fc_E_phi = float(self.config.get(mdl_type, "E_phi", fallback=42.7))
        self.fc_b1 = float(self.config.get(mdl_type, "b1", fallback=1.55e-5))
        self.fc_LHV_H2 = float(self.config.get(mdl_type, "LHV_H2", fallback=120000))
        self.fc_ser_wght = float(self.config.get(mdl_type, "service_weight", fallback=1.0))
        self.is_P_priority = self.bool_check(self.config.get(mdl_type, "is_P_priority", fallback=True))
        self.FW21_Enabled = self.bool_check(self.config.get(mdl_type, "FW21_Enabled", fallback=False))
        self.is_autonomous = self.bool_check(self.config.get(mdl_type, "is_autonomous", fallback=False))
        self.fc_db_UF = float(self.config.get(mdl_type, "db_UF", fallback=0.36))
        self.fc_db_OF = float(self.config.get(mdl_type, "db_OF", fallback=0.36))
        self.fc_k_UF = float(self.config.get(mdl_type, "k_UF", fallback=0.05))
        self.fc_k_OF = float(self.config.get(mdl_type, "k_OF", fallback=0.05))
        self.__P_pre = float(self.config.get(mdl_type, "P_pre", fallback=-1.0))

        # Establish the grid locations that the fuel cell fleet is connected in the grid
        if isinstance(grid_info, GridInfo):
            self.grid = grid_info
        else:
            # Set services to false if GridInfo is not called correctly during fleet init.
            self.is_P_priority = True
            self.is_autonomous = False
            self.FW21_Enabled = False
            warn("GridInfo() needs to be loaded with AI data. "
                 "Please check your FuelCell fleet initialization code!! "
                 "Fleet services will be set to False")

        # Pre-load a base profile for the Electrolyer based on price-demand response curve
        self.fc_pbase = join(self.base_path, self.config.get(mdl_type, "power_data", fallback="Pbase.txt"))

        if self.config.sections()[0] != mdl_type:
            print("Error reading config.ini file for model:"+"\t"*3+"%s [FAIL]!!" % mdl_type)
            print("Model found in config.ini file:"+"\t"*5+"%s!!\n"
                  "Default modelling parameters will be used!!\n" % self.config.sections()[0])
        else:
            print("Model parameters found for:"+"\t"*5+"%s [OKAY]\n" % self.config.sections()[0])

        # Compute state parameters for the FuelCell fleet model
        self.f = None
        self.__Vi = self.__Ir = self.__Vr_age = self.__Ir_age = self.__p_base = 0.0
        self.__V_act = self.__Ii = self.__Vr = self.__Ir_age = self.__id0 = 0.0
        self.__expo = self.__conv = self.__ne = self.__ne_age = 0.0
        self.__ed_cell = self.__e_cell = self.__p_tot_ideal = self.__p_tot_age = 0.0
        self.__Qh2_m = self.__Qh2_m_age = 0.0
        self.__m_dotH2 = self.__m_dotH2_age = 0.0
        self.lka_h2 = self.__Phi = 0.0
        self.__eta_ds = 0.0
        self.__inc = 0

        self.fleet_rating = self.fc_Nfc*self.fc_size

        # Set the operating range for the FuelCell default fleet - 6kW <= Pfc <= 240kW
        self.P_opt = lambda p_req, p_min, p_max: max(p_min, min(p_max, p_req))

        # Operating temperature of FuelCell in deg. C.
        self.fc_T += 273.15

        # Min. state of charge in the hydrogen tank
        self.min_charge = self.fc_charge_lvl_min*1e-2*self.fc_Pe_out

        # Max. state of charge in the hydrogen tank
        self.max_charge = self.fc_charge_lvl_max*1e-2*self.fc_Pe_out

        # Initial state of charge (pressure) in the tank w/ and w/o aging
        self.P_tank_ideal = self.P_tank_age = self.soc_ideal = self.soc_age = self.max_charge

        # Initial number of H2 moles in the tank w/ and w/o aging
        self.ni = (self.P_tank_ideal*self.fc_V_tank/self.fc_R/(self.fc_Ts+273.15))*self.fc_Nt

        # initial moles w/ and w/o ageing
        self.moles_ideal = self.moles_age = self.ni

        self.DG = self.fc_DG_200+(200-self.fc_T+273.15)/175*(self.fc_DG_25-self.fc_DG_200)
        self.V_rev = self.DG/self.fc_ne0/self.fc_F

        # Thermo-neutral voltage
        self.Vtn = self.fc_DH/self.fc_ne0/self.fc_F
        # (A)
        self.b1 = self.fc_b/self.fc_A
        # (A)
        self.i_n1 = self.fc_i_n*self.fc_A
        # (A)
        self.i_01 = self.fc_i_0*self.fc_A
        # (Ohm)
        self.R_tot1 = self.fc_R_tot/self.fc_A
        self.fc_At *= self.fc_Nt
        self.fc_len /= 1e3

        # Fit the base power profile for FuelCell
        self.p = self.fit_pdat(self.fc_pbase, 5 * 60)

        # Output metrics dataframe
        self.metrics = [['ts', 'Vr_ideal', 'Vr_age', 'ne_ideal', 'ne_age', 'Soc_ideal', 'Soc_age', 'Lka_H2', 'nds']]

    def process_request(self, fleet_request):
        resp = self.fc_model(fleet_request.ts_req, fleet_request.sim_step,
                             fleet_request.P_req, False, fleet_request.start_time)
        return resp

    def forecast(self, requests):
        soc_state, soc_state_age, state = self.soc_ideal, self.soc_age, self.__inc
        resp = [self.fc_model(req.ts_req, req.sim_step, req.P_req, True, req.start_time) for req in requests]
        self.soc_ideal, self.soc_age, self.__inc = soc_state, soc_state_age, state
        return resp

    def fc_model(self, ts, sim_step, Preq, forecast=False, start_time=None):
        """
        :param ts: Request created for current time-step: datetime
        :param sim_step: Request for simulation time-step: timedelta object
        :param Preq: Request for current real power request
        :param forecast: Returns fleet response forecast
        :param start_time: Request for current real power request
        :return resp: Fleet response object
        """

        if self.P_tank_ideal <= self.min_charge:
            pass
        else:

            # Create base power profile
            if isinstance(self.p, ndarray):
                self.__p_base = sum([self.p[j] * (self.__inc + 1) ** (21 - j) for j in range(22)])
            else:
                self.__p_base = self.p
            # Ptogrid: Pbase for None or zero requests since FC is a source
            if Preq is None or float(Preq) == 0.0:
                Preq = self.__p_base
            # Ptogrid: Preq+Pbase for +ve or -ve requests
            else:
                Preq += self.__p_base
            # Compute the power generated by the fleet
            self.__fc_p_calc(Preq)

            if self.FW21_Enabled and self.is_autonomous:
                # all in kW
                Preq, self.f = self.frequency_watt(p_pre=self.__p_tot_ideal, p_avl=self.fc_Pmax_fleet,
                                                   p_min=self.fc_Pmin_fleet,
                                                   ts=ts, start_time=start_time)
                self.__p_tot_ideal = Preq

            # Update SOC
            self.__soc_calc()
        self.__inc += 1

        # Response
        # Power injected is positive
        resp = FleetResponse()
        resp.ts = ts
        resp.sim_step = sim_step
        resp.C = 0
        resp.dT_hold_limit = 0
        resp.E = self.soc_ideal
        resp.Eff_charge = 1.0
        resp.Eff_discharge = self.__eta_ds
        resp.P_dot_down = 0
        resp.P_dot_up = 0
        resp.P_togrid = self.__p_tot_ideal
        resp.P_togrid_max = self.fc_Pmax_fleet
        resp.P_togrid_min = self.fc_Pmin_fleet
        resp.P_service = resp.P_togrid - self.__p_base
        resp.P_service_max = self.fc_Pmax_fleet-self.__p_base
        resp.P_service_min = self.__p_base-self.fc_Pmin_fleet
        resp.Q_dot_down = 0
        resp.Q_dot_up = 0
        resp.Q_service = 0
        resp.Q_service_max = 0
        resp.Q_service_min = 0
        resp.Q_togrid = 0
        resp.Q_togrid_max = 0
        resp.Q_togrid_min = 0
        resp.T_restore = 0
        resp.P_base = self.__p_base
        resp.Q_base = 0
        resp.Strike_price = 0
        resp.SOC_cost = 0

        # Impact metrics
        if not forecast:
            self.metrics.append([str(ts), str(self.__Vr), str(self.__Vr_age), str(self.__ne),
                                 str(self.__ne_age), str(self.soc_ideal * 1e2), str(self.soc_age * 1e2),
                                 str(self.lka_h2), str(self.__eta_ds * 1e2)])

        # Print Soc every 5 secs.
        if self.__inc % 5000 == 0:
            print("Soc:%4.2f%%" % (resp.E*1e2))

        return resp

    def output_metrics(self, filename):
        base_path = dirname(abspath(__file__))
        with open(join(base_path, str(filename)+'.csv'), 'w', newline='') as out:
            write = writer(out)
            write.writerows(self.metrics)
            print("Impact metrics created has been created"+"\t"*5+" [OKAY]\n")

    def output_impact_metrics(self, service_name):        
        metrics_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'integration_test', service_name)
        ensure_ddir(metrics_dir)
        metrics_filename = 'ImpactMetrics_' + service_name + '_FuelCell' + '_' + datetime.now().strftime('%Y%m%dT%H%M')  + '.csv'
        with open(join(metrics_dir, metrics_filename), 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self.metrics)     

    def assigned_service_kW(self):
        return self.fc_ser_wght*self.fleet_rating

    @staticmethod
    def __vifc_calc(x, Pri, V_rev, T, R, alpha, F, i_n, i_0, R_tot, a, b, pH2, pO2):
        Vact = (R*T/alpha/F)*log((x[1]+i_n)/i_0)
        Vohm = (x[1] + i_n)*R_tot
        Vcon = a*exp(b*x[1])
        E_cell = V_rev+R*T/2/F*log(pH2*pO2**0.5)
        fb = list([x[0]-E_cell+Vact+Vohm-Vcon])
        fb.append(x[0]*x[1]-Pri)
        return fb

    def __fc_p_calc(self, p_req):
        # Check for operating range of the fleet
        Preq = float(self.P_opt(abs(p_req), self.fc_Pmin_fleet, self.fc_Pmax_fleet))

        Pr = abs(Preq) * 1e3 / self.fc_Nfc / self.fc_Nc  # Watts
        # Compute voltage and current for 1 FuelCell stack
        self.__Vi, self.__Ir = fsolve(self.__vifc_calc, [self.fc_x01, self.fc_x02],
                                      args=(Pr, self.V_rev, self.fc_T,
                                            self.fc_R, self.fc_alpha, self.fc_F, self.i_n1,
                                            self.i_01, self.R_tot1, self.fc_a, self.b1,
                                            self.fc_pH2, self.fc_pO2))

        self.__Vact = (self.fc_R * self.fc_T / self.fc_alpha / self.fc_F) * log((self.__Ir + self.i_n1) / self.i_01)
        self.__Vohm = (self.__Ir + self.i_n1) * self.R_tot1
        self.__Vcon = self.fc_a * exp(self.b1 * self.__Ir)
        self.__Ii = self.__Ir * 1e3 / self.fc_A
        self.__id0 = self.__Ir / self.fc_A
        self.__expo = exp(self.__inc / self.fc_Tau_e)
        self.__conv = convolve(self.__id0, self.__expo)[0]
        self.__Ed_cell = self.fc_Lambda * (self.__id0 - self.__conv)
        self.__E_cell = self.V_rev + self.fc_R * self.fc_T / 2 / self.fc_F * log(self.fc_pH2 * self.fc_pO2 ** 0.5) - self.__Ed_cell

        self.__Vr = self.__E_cell - self.__Vact - self.__Vohm + self.__Vcon
        # if Vr > Vi:   Vr = Vi
        self.__Vr = min(self.__Vr, self.__Vi)
        self.__Vr_age = self.__Vr - 5.28489722540435e-15 * (self.__inc + 1) ** 2 - 5.36476231386010e-08 * (self.__inc + 1)
        self.__Ir_age = Pr / self.__Vr_age
        self.__ne = self.__Vr / 1.48
        self.__ne_age = self.__Vr_age / 1.48
        # (kW)
        self.__p_tot_ideal = self.__Vr * self.__Ir * self.fc_Nfc * self.fc_Nc * 1e-3
        self.__p_tot_age = self.__Vr_age * self.__Ir_age * self.fc_Nfc * self.fc_Nc * 1e-3

    def __soc_calc(self):

        # Flow of H2 consumed
        self.__Qh2_m = self.fc_Nfc * self.fc_Nc * self.__Ir / 2 / self.fc_F  # (mol/s)
        self.__Qh2_m_age = self.fc_Nfc * self.fc_Nc * self.__Ir_age / 2 / self.fc_F  # (mol/s)
        self.__m_dotH2 = self.__Qh2_m * 2 / 1e3  # (kg/s)
        self.__m_dotH2_age = self.__Qh2_m_age * 2 / 1e3  # (kg/s)

        # Storage Tank
        # Number of moles in time i in the tank
        self.moles_ideal -= self.__Qh2_m * 1
        self.P_tank_ideal = self.moles_ideal / self.fc_Nt * self.fc_R * (self.fc_Ts + 273.15) / self.fc_V_tank
        self.soc_ideal = self.P_tank_ideal / self.max_charge

        # Compute hydrogen leakage from tank
        self.__Phi = self.fc_Phi_0 * exp(
            -self.fc_E_phi / (self.fc_R * 1e-3) / (self.fc_Ts + 273.15))  # (mol s^-1 m^-1 MPa^-0.5)
        # fugacity
        f = self.P_tank_ideal * 1e-6 * exp(
            self.P_tank_ideal * 1e-6 * self.fc_b1 / (self.fc_R * 1e-3) / (self.fc_Ts + 273.15))
        J = self.__Phi / self.fc_len * 2 * f ** 0.5  # (g m^-2 s^-1)
        lk_H2 = J * self.fc_At  # (g/s)
        # total hydrogen lost in time t (g)
        self.lka_h2 += J * self.fc_At * 1
        self.moles_age -= self.__Qh2_m_age * 1 - self.lka_h2 / 2 * 1
        self.P_tank_age = self.moles_age / self.fc_Nt * self.fc_R * (self.fc_Ts + 273.15) / self.fc_V_tank
        self.soc_age = self.P_tank_age / self.max_charge

        # Discharging efficiency
        self.__eta_ds = self.__p_tot_ideal * 1e3 / self.fc_LHV_H2 / (self.__m_dotH2 * 1e3)  # (W/W)

        if self.soc_ideal > 1.0 or self.soc_ideal < 0.0:
            sys.exit(print("Soc limit violation!!" + "\t" * 6 + " [!!]\n"))

    @staticmethod
    def bool_check(b_in):
        if str(b_in) in ('TRUE', 'True', 'T', 't', 'Yes', 'YES', 'y', 'yes'):
            return True
        elif str(b_in) in ('FALSE', 'False', 'F', 'f', 'No', 'NO', 'n', 'no'):
            return False
        else:
            return ValueError('%s is not Boolean. Please set True/False in config.ini' % b_in)

    def frequency_watt(self, p_pre=1.0, p_avl=1.0, p_min=0.1, ts=datetime.utcnow(), location=0, start_time=None):
        f = self.grid.get_frequency(ts, location, start_time)
        P_pre = p_pre / self.fc_Pmax_fleet
        P_avl = p_avl / self.fc_Pmax_fleet
        P_min = p_min / self.fc_Pmax_fleet
        if f < 60 - self.fc_db_UF:
            p_set = min(P_pre+((60-self.fc_db_UF)-f)/(60*self.fc_k_UF),P_avl)
        elif f > 60 + self.fc_db_OF:
            p_set = max(P_pre-(f-(60+self.fc_db_OF))/(60*self.fc_k_OF),P_min)
        else:
            p_set = P_avl
        p_set *= self.fc_Pmax_fleet
        return p_set, f

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
                # Set Pbase as an average of Pmin and Pmax operating range of a single FuelCell fleet
                p_val = sum([self.fc_Pmax_fleet + self.fc_Pmin_fleet]) / 2.0
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
        fig1.savefig(join(base_path, "FC_result_%s.png" % str(datetime.utcnow().strftime('%d_%b_%Y_%H_%M_%S'))),
                     bbox_inches='tight')
