# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
Description: This class implements the FuelCell FleetInterface to integrate with a fleet of
FuelCells
"""

from _load import *
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from fleet_interface import FleetInterface
simplefilter('ignore', RankWarning)
colorama.init()


class FuelCellFleet(FleetInterface):
    """
    FuelCell Fleet Class
    """

    def __init__(self, grid_info, mdl_config="config.ini", mdl_type="FuelCell", p_req=None, **kwargs):
        """
        :param GridInfo: GridInfo object derived from the GridInfo Class
        :param mdl_type: Model parameters to be loaded from config.ini
        :param p_req: Use instantaneous power request. Default is None.
        :param kwargs:
        """

        # Establish the grid locations that the fuelcell fleet is connected to
        self.grid = grid_info

        if not p_req:
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
        self.fc_Pe = float(self.config.get(mdl_type, "Pe", fallback=101000))
        self.fc_Pe_out = float(self.config.get(mdl_type, "Pe_out", fallback=50000000))
        self.fc_size = float(self.config.get(mdl_type, "Fc_size", fallback=1.6))
        self.fc_A = float(self.config.get(mdl_type, "A", fallback=200))
        self.fc_Nc = float(self.config.get(mdl_type, "Nc", fallback=20))
        self.fc_F = float(self.config.get(mdl_type, "F", fallback=96485.34))
        self.fc_ne0 = float(self.config.get(mdl_type, "ne0", fallback=2))
        self.fc_charge_lvl_min = float(self.config.get(mdl_type, "charge_lvl_min", fallback=19))
        self.fc_charge_lvl_max = float(self.config.get(mdl_type, "charge_lvl_max", fallback=95))
        self.fc_soc_lvl_init = float(self.config.get(mdl_type, "soc_lvl_init", fallback=95))
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
        self.fc_T += 273.15
        # min. state of charge in the hydrogen tank
        self.min_charge = self.fc_charge_lvl_min*1e-2*self.fc_Pe_out
        # max. state of charge in the hydrogen tank
        self.max_charge = self.fc_charge_lvl_max*1e-2*self.fc_Pe_out
        # SOC initial
        self.soc_i = self.fc_soc_lvl_init*1e-2*self.fc_Pe_out
        # initial number of H2 moles in the tank
        self.moles = (self.soc_i*self.fc_V_tank/self.fc_R/(25+273.15))*self.fc_Nt
        self.P_tank = self.soc_i
        self.DG = self.fc_DG_200+(200-self.fc_T+273.15)/175*(self.fc_DG_25-self.fc_DG_200)
        self.V_rev = self.DG/self.fc_ne0/self.fc_F
        self.inc = 0

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

        if self.load_curve:
            # Fit the power curve input data
            self.p, self.timespan = fit_pdat(self.fc_pdat)
        self.inc = 0

    def process_request(self, request):
        resp = self.fc_model(request)
        return resp

    def fc_model(self, req):
        resp = FCResponse()

        resp.ts = self.inc
        if self.load_curve:
            # Power profile (kW)
            resp.Pl = sum([self.p[j]*(self.inc+1)**(21-j) for j in range(22)])
            # (W) requested power for one cell
            resp.Pr = 1e3*resp.Pl/self.fc_Nfc/self.fc_Nc
        else:
            if self.inc == 0:
                self.fc_Nfc = int(req/self.fc_size)
                cprint("No. of FuelCells used is:"+"\t"*5+"%d" % self.fc_Nfc, 'green')
            resp.Pr = 1e3*req/self.fc_Nfc/self.fc_Nc

        resp.Vi, resp.Ir = fsolve(vifc_calc, [self.fc_x01, self.fc_x02],
                                 args=(resp.Pr, self.V_rev, self.fc_T,
                                       self.fc_R, self.fc_alpha, self.fc_F, self.i_n1,
                                       self.i_01, self.R_tot1, self.fc_a, self.b1,
                                       self.fc_pH2, self.fc_pO2))

        resp.Vact = (self.fc_R*self.fc_T/self.fc_alpha/self.fc_F)*log((resp.Ir+self.i_n1)/self.i_01)
        resp.Vohm = (resp.Ir+self.i_n1)*self.R_tot1
        resp.Vcon = self.fc_a*exp(self.b1*resp.Ir)
        #resp.V_graph = self.V_rev - resp.Vact - resp.Vohm + resp.Vcon
        resp.Ii = resp.Ir*1e3/self.fc_A
        resp.id0 = resp.Ir/self.fc_A
        expo = exp(self.inc/self.fc_Tau_e)
        conv = convolve(resp.id0, expo)
        resp.Ed_cell = self.fc_Lambda*(resp.id0-conv)
        resp.E_cell = self.V_rev+self.fc_R*self.fc_T/2/self.fc_F*log(self.fc_pH2*self.fc_pO2**0.5)-resp.Ed_cell
        resp.Vr = resp.E_cell-resp.Vact-resp.Vohm+resp.Vcon
        if resp.Vr > resp.Vi:
            resp.Vr = resp.Vi
        resp.Videal = resp.Vi
        resp.Vreal = resp.Vr

        # (kW)
        resp.P = resp.Vr*resp.Ir*self.fc_Nfc*self.fc_Nc/1000
        resp.ne = (resp.Vr/1.48)*1e2
        # (mol/s)
        resp.Qh2_m = self.fc_Nfc*self.fc_Nc*resp.Ir/2/self.fc_F

        # Storage Tank
        # Number of moles in time i in the tank
        self.moles = self.moles-resp.Qh2_m*1
        resp.moles = self.moles
        resp.P_tank = self.moles*self.fc_R*(self.fc_T+273.15)/self.fc_V_tank
        resp.soc = resp.P_tank
        resp.soc_per = resp.soc/self.max_charge*100
        resp.isAvail = True
        if resp.soc < self.min_charge:
            cprint('Discharge time:' + '\t' * 7 + '%dsec.' % self.inc, 'green')
            soc_i = round((resp.soc/self.max_charge * 100), 1)
            cprint('State of Charge:' + '\t' * 6 + '%d%%' % soc_i, 'green')
            cprint('Tank is fully discharged!!', 'cyan')
            resp.isAvail = False
        self.inc += 1
        return resp


class FCResponse:
    """
    This class provides one time-step output for FuelCells based on time-series
    input power curve
    """
    def __init__(self):
        self.ts = 0
        self.Pr = 0
        self.Vi = 0
        self.Ir = 0
        self.Vact = 0
        self.Vohm = 0
        self.Vcon = 0
        self.Ii = 0
        self.id0 = 0
        self.Ed_cell = 0
        self.E_cell = 0
        self.Vr = 0
        self.Videal = 0
        self.Vreal = 0
        self.P = 0
        self.ne = 0
        self.Qh2_m = 0
        self.P_tank = 0
        self.moles = 0
        self.soc = 0
        self.soc_per = 0
        self.isAvail = True


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
    fig1 = figure(figsize=(20, 8))
    fig1.subplots_adjust(wspace=0.4)
    fig1.subplots_adjust(hspace=4.5)
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
    show()
    fig1.savefig(join(base_path, "fc_result.png"), bbox_inches='tight')
