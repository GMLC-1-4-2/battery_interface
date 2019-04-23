# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
Description: This class implements the FuelCell FleetInterface to integrate with a fleet of
FuelCells
"""

import sys
from os.path import dirname, abspath, join
from warnings import simplefilter, filterwarnings
import colorama
from termcolor import cprint
import configparser
from numpy import polyfit, convolve, RankWarning, log, exp
from pandas import read_csv
from scipy.optimize import fsolve
from matplotlib.pyplot import figure, subplot2grid, savefig
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from fleet_interface import FleetInterface
from fleet_response  import FleetResponse
from csv import writer
simplefilter('ignore', RankWarning)
filterwarnings("ignore", category=RuntimeWarning)
colorama.init()


class FuelCellFleet(FleetInterface):
    """
    FuelCell Fleet Class
    """

    def __init__(self, grid_info, mdl_config="config.ini", mdl_type="FuelCell", p_req_load=None, **kwargs):
        """
        :param GridInfo: GridInfo object derived from the GridInfo Class
        :param mdl_type: Model parameters to be loaded from config.ini
        :param p_req_load: Use instantaneous power request. Default is None.
        :param kwargs:
        """

        # Establish the grid locations that the fuel cell fleet is connected in the grid
        # Not being used in the present scenario to provide grid services
        self.grid = grid_info

        if p_req_load:
            self.load_curve = True
        else:
            self.load_curve = False

        # Load the config file that has model parameters
        base_path = dirname(abspath(__file__))
        self.config = configparser.ConfigParser()
        self.config.read(join(base_path, mdl_config))

        # Read the model parameters from config file with defaults as fallback
        self.fc_model_name = self.config.get(mdl_type, "Name", fallback="Default FuelCell Fleet")
        self.fc_T = float(self.config.get(mdl_type, "T", fallback=70))
        self.fc_Ts = float(self.config.get(mdl_type, "Ts", fallback=25))
        self.fc_Pe = float(self.config.get(mdl_type, "Pe", fallback=101000))
        self.fc_Pe_out = float(self.config.get(mdl_type, "Pe_out", fallback=50000000))
        self.fc_Pe_base = float(self.config.get(mdl_type, "Pe_base", fallback=0.0))
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

        # Will pre-load the power curve input data if P_req is not set. User will have to provide
        # a time-stamped CSV data file that has the power input data
        if self.load_curve:
            self.fc_pdat = join(base_path, self.config.get(mdl_type, "power_data", fallback="pdata.csv"))
        if self.config.sections()[0] != mdl_type:
            cprint("Error reading config.ini file for model:"+"\t"*3+"%s [FAIL]!!" % mdl_type, 'red',)
            print("Model found in config.ini file:"+"\t"*5+"%s!!\n"
                  "Default modelling parameters will be used!!\n" % self.config.sections()[0])
        else:
            cprint("Model parameters found for:"+"\t"*5+"%s [OKAY]\n" % self.config.sections()[0], 'green')

        # Compute state parameters for the FuelCell model
        self.fleet_rating = self.fc_Nfc*self.fc_size
        # Set the operating range for the Electrolyzer fleet - 6kW <= Pfc <= 240kW
        self.P_opt = lambda p_req, p_min, p_max: max(p_min, min(p_max, p_req))
        self.fc_T += 273.15
        # min. state of charge in the hydrogen tank
        self.min_charge = self.fc_charge_lvl_min*1e-2*self.fc_Pe_out
        # max. state of charge in the hydrogen tank
        self.max_charge = self.fc_charge_lvl_max*1e-2*self.fc_Pe_out
        # Initial state of charge (pressure) in the tank
        self.P_tank_ideal = self.max_charge
        self.P_tank_age = self.max_charge
        # SOC initial
        self.soc_ideal = self.P_tank_ideal
        self.soc_age = self.P_tank_ideal
        # Initial number of H2 moles in the tank
        self.ni = (self.P_tank_ideal*self.fc_V_tank/self.fc_R/(self.fc_Ts+273.15))*self.fc_Nt
        # initial moles w/o ageing
        self.moles_ideal = self.ni
        # initial moles w/ ageing
        self.moles_age = self.ni
        self.DG = self.fc_DG_200+(200-self.fc_T+273.15)/175*(self.fc_DG_25-self.fc_DG_200)
        self.V_rev = self.DG/self.fc_ne0/self.fc_F
        # Leakage
        self.lka_h2 = 0
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
        if self.load_curve:
            # Fit the power curve input data
            self.p, self.timespan = fit_pdat(self.fc_pdat)
        # Output metrics dataframe
        self.metrics = [['ts', 'Vr_ideal', 'Vr_age', 'ne_ideal', 'ne_age', 'Soc_ideal', 'Soc_age', 'Lka_H2', 'nds']]
        self.inc = 0

    def process_request(self, fleet_request):
        resp = self.fc_model(fleet_request.ts_req, fleet_request.sim_step, fleet_request.P_req)
        return resp

    def forecast(self, requests):
        soc_state, soc_state_age = self.soc_ideal, self.soc_age
        resp = [self.fc_model(req.ts_req, req.sim_step, req.P_req) for req in requests]
        self.soc_ideal, self.soc_age = soc_state, soc_state_age
        return resp

    def fc_model(self, ts, sim_step, Preq):
        resp = FleetResponse()

        if self.P_tank_ideal <= self.min_charge:
            is_avail, resp.fc_fleet, P_tot_ideal, ne, nf, Vr, Vi, Ir, eta_ds =\
                0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        else:
            if self.load_curve and Preq is None:
                # Power profile (kW)
                Pl = sum([self.p[j]*(self.inc+1)**(21-j) for j in range(22)])
                # (W) requested power for one cell
                Pr = 1e3*Pl/self.fc_Nfc/self.fc_Nc
            # Only respond to positive power request when Preq is present
            elif Preq is None or Preq <= 0:
                Pr = abs(self.fc_Pmin_fleet)*1e3/self.fc_Nfc/self.fc_Nc
            else:
                # Check if Preq is within operational range in kW
                # Fleet size remains constant
                Preq = self.P_opt(abs(Preq), self.fc_Pmin_fleet, self.fc_Pmax_fleet)
                Pr = Preq*1e3/self.fc_Nfc/self.fc_Nc  # Watts
            resp.fc_fleet = int(self.fc_Nfc)
            # Compute voltage and current for 1 FuelCell stack
            Vi, Ir = fsolve(vifc_calc, [self.fc_x01, self.fc_x02],
                            args=(Pr, self.V_rev, self.fc_T,
                                  self.fc_R, self.fc_alpha, self.fc_F, self.i_n1,
                                  self.i_01, self.R_tot1, self.fc_a, self.b1,
                                  self.fc_pH2, self.fc_pO2))

            Vact = (self.fc_R*self.fc_T/self.fc_alpha/self.fc_F)*log((Ir+self.i_n1)/self.i_01)
            Vohm = (Ir+self.i_n1)*self.R_tot1
            Vcon = self.fc_a*exp(self.b1*Ir)
            Ii = Ir*1e3/self.fc_A
            id0 = Ir/self.fc_A
            expo = exp(self.inc/self.fc_Tau_e)
            conv = convolve(id0, expo)
            Ed_cell = self.fc_Lambda*(id0-conv)
            E_cell = self.V_rev+self.fc_R*self.fc_T/2/self.fc_F*log(self.fc_pH2*self.fc_pO2**0.5)-Ed_cell
            Vr = E_cell-Vact-Vohm+Vcon
            #if Vr > Vi:
            #    Vr = Vi
            Vr = min(Vr, Vi)
            Vr_age = Vr-5.28489722540435e-15*(self.inc+1)**2-5.36476231386010e-08*(self.inc+1)
            Ir_age = Pr/Vr_age
            # (kW)
            P_tot_ideal = Vr*Ir*self.fc_Nfc*self.fc_Nc*1e-3
            P_tot_age = Vr_age*Ir_age*self.fc_Nfc*self.fc_Nc*1e-3
            ne = (Vr/1.48)*1e2
            ne_age = (Vr_age/1.48)*1e2

            # Flow of H2 consumed
            Qh2_m = self.fc_Nfc*self.fc_Nc*Ir/2/self.fc_F           # (mol/s)
            Qh2_m_age = self.fc_Nfc*self.fc_Nc*Ir_age/2/self.fc_F   # (mol/s)
            m_dotH2 = Qh2_m*2/1e3                                   # (kg/s)
            m_dotH2_age = Qh2_m_age*2/1e3                           # (kg/s)

            # Storage Tank
            # Number of moles in time i in the tank
            self.moles_ideal -= Qh2_m*1
            self.P_tank_ideal = self.moles_ideal/self.fc_Nt*self.fc_R*(self.fc_Ts+273.15)/self.fc_V_tank
            self.soc_ideal = self.P_tank_ideal/self.max_charge

            # Compute hydrogen leakage from tank
            Phi = self.fc_Phi_0*exp(-self.fc_E_phi/(self.fc_R*1e-3)/(self.fc_Ts+273.15))  # (mol s^-1 m^-1 MPa^-0.5)
            # fugacity
            f = self.P_tank_ideal*1e-6*exp(self.P_tank_ideal*1e-6*self.fc_b1/(self.fc_R*1e-3)/(self.fc_Ts+273.15))
            J = Phi/self.fc_len*2*f**0.5  # (g m^-2 s^-1)
            lk_H2 = J*self.fc_At  # (g/s)
            # total hydrogen lost in time t (g)
            self.lka_h2 += J*self.fc_At*1
            self.moles_age += Qh2_m_age * 1 - self.lka_h2 / 2 * 1
            self.P_tank_age = self.moles_age/self.fc_Nt*self.fc_R*(self.fc_Ts + 273.15)/self.fc_V_tank
            self.soc_age = self.P_tank_age/self.max_charge

            # Discharging efficiency
            eta_ds = P_tot_ideal*1e3/self.fc_LHV_H2/(m_dotH2*1e3)          # (W/W)
            is_avail = 1

        self.inc += 1

        # Response
        # Power injected is positive

        resp.ts = ts
        resp.sim_step = sim_step
        resp.C = None
        resp.dT_hold_limit = None
        resp.E = self.soc_ideal*1e2  # SoC in %
        resp.Eff_charge = None
        resp.Eff_discharge = eta_ds*1e2
        resp.P_dot_down = 0
        resp.P_dot_up = 0
        resp.P_service = P_tot_ideal+self.fc_Pe_base
        resp.P_service_max = 0
        resp.P_service_min = 0
        resp.P_togrid = P_tot_ideal
        resp.P_togrid_max = self.fc_Pmax_fleet
        resp.P_togrid_min = self.fc_Pmin_fleet
        resp.Q_dot_down = None
        resp.Q_dot_up = None
        resp.Q_service = None
        resp.Q_service_max = None
        resp.Q_service_min = None
        resp.Q_togrid = 0
        resp.Q_togrid_max = None
        resp.Q_togrid_min = None
        resp.T_restore = 0
        resp.status = is_avail
        resp.V = Vr
        resp.Ir = Ir
        resp.ne = ne

        # Impact metrics
        self.metrics.append([str(ts), str(Vr), str(Vr_age), str(ne),
                             str(ne_age), str(self.soc_ideal * 1e2), str(self.soc_age[0] * 1e2),
                             str(self.lka_h2), str(eta_ds * 1e2)])

        # Print Soc every 5 secs.
        if self.inc % 5000 == 0:
            print("Soc:%4.2f%%" % resp.E)

        return resp

    def output_metrics(self, filename):
        base_path = dirname(abspath(__file__))
        with open(join(base_path, str(filename)+'.csv'), 'w', newline='') as out:
            write = writer(out)
            write.writerows(self.metrics)
            cprint("Impact metrics created"+"\t"*5+" [OKAY]\n", 'green')

    def assigned_service_kW(self):
        return self.fc_ser_wght*self.fleet_rating


def fit_pdat(filename, time_interval=None):
    """
    Read demand profile and check if timestamp interval is at least in seconds.
    Execute only if freq does not match: milli, micro, or nano
    :param filename: Time-stamped power curve input data as CSV
    :param time_interval: Specify the data time interval in seconds
    :return p: Curve-fit results using Least square curve-fitting method
    """
    if time_interval is None:
        try:
            df = read_csv(filename, header=None, parse_dates=[0], index_col=0, nrows=10)
            interval = df.index.inferred_freq
        except (AttributeError, TypeError):
            raise Exception("\tUnable to infer time interval from input data\n"
                            "\tPlease specify the time_interval parameter in seconds!!\n")
        if any(i in interval for i in ('L', 'ms', 'U', 'us', 'N')) is False:
            cprint("Power data time-interval is at least in seconds:\t\t[OKAY]", 'green')
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
        df = read_csv(filename, header=None, names=['Pval'])
        df['sec'] = [i for i in range(0, len(df)*time_interval, time_interval)]

    # Least-square curve-fitting
    return polyfit(df['sec'].values, df['Pval'].values, 21), int(df['sec'].iloc[-1])


def vifc_calc(x, Pri, V_rev, T, R, alpha, F, i_n, i_0, R_tot, a, b, pH2, pO2):
    Vact = (R*T/alpha/F)*log((x[1]+i_n)/i_0)
    Vohm = (x[1] + i_n)*R_tot
    Vcon = a*exp(b*x[1])
    E_cell = V_rev+R*T/2/F*log(pH2*pO2**0.5)
    fb = list([x[0]-E_cell+Vact+Vohm-Vcon])
    fb.append(x[0]*x[1]-Pri)
    return fb


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
    fig1.savefig(join(base_path, "FC_result.png"), bbox_inches='tight')
