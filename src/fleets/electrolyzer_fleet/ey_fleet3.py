# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
Description: This class implements the Electrolyzer FleetInterface to integrate with a fleet of
Electrolyzers
"""

from _load import *
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from fleet_interface import FleetInterface
from ey_response import EYResponse
from helpers import fit_pdat, vi_calc, ne_calc
colorama.init()


class ElectrolyzerFleet(FleetInterface):
    """
    Electrolyzer Fleet Class
    ToDO: Include current power request processing.
    """

    def __init__(self, grid_info, mdl_config="config.ini", mdl_type="Electrolyzer", p_req=None, **kwargs):
        """
        :param GridInfo: GridInfo object derived from the GridInfo Class
        :param mdl_type: Default model parameter values
        :param kwargs:
        """

        # Establish the grid locations that the electrolyzer fleet is connected in the grid
        # Not being used in the present scenario to provide grid services
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
        self.ey_charge_lvl_min = float(self.config.get(mdl_type, "charge_lvl_min", fallback=20))
        self.ey_charge_lvl_max = float(self.config.get(mdl_type, "charge_lvl_max", fallback=95))
        self.ey_soc_lvl_init = float(self.config.get(mdl_type, "soc_lvl_init", fallback=19))
        self.ey_DG_25 = float(self.config.get(mdl_type, "DG_25", fallback=237000.0))
        self.ey_DG_80 = float(self.config.get(mdl_type, "DG_80", fallback=228480.0))
        self.ey_DH = float(self.config.get(mdl_type, "DH", fallback=286000.0))
        self.ey_R = float(self.config.get(mdl_type, "R", fallback=8.31445))
        self.ey_Ne = float(self.config.get(mdl_type, "Ne", fallback=54))
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
        # Will pre-load the power curve input data if P_req is not set. User will have to provide
        # a time-stamped CSV data file that has the power input data
        if self.load_curve:
            self.ey_pdat = join(base_path, self.config.get(mdl_type, "power_data", fallback="pdata.csv"))
        if self.config.sections()[0] != mdl_type:
            cprint("Error reading config.ini file for model:"+"\t"*3+"%s [FAIL]!!" % mdl_type, 'red',)
            print("Model found in config.ini file:"+"\t"*5+"%s!!\n"
                  "Default modelling parameters will be used!!\n" % self.config.sections()[0])
        else:
            cprint("Model parameters found for:"+"\t"*5+"%s [OKAY]\n" % self.config.sections()[0], 'green')

        # Compute state parameters for the Electrolyzer model
        # min. state of charge in the hydrogen tank
        self.min_charge = self.ey_charge_lvl_min*1e-2*self.ey_Pe_out
        # max. state of charge in the hydrogen tank
        self.max_charge = self.ey_charge_lvl_max*1e-2*self.ey_Pe_out
        # SOC initial
        self.soc_i = self.ey_soc_lvl_init*1e-2*self.ey_Pe_out
        # moles[0][0] = n_i
        self.moles = self.soc_i*self.ey_V_tank/self.ey_R/(self.ey_T+273.15)
        self.DG = self.ey_DG_25-(self.ey_T-25)/55*(self.ey_DG_25-self.ey_DG_80)
        self.V_rev = self.DG/self.ey_ne0/self.ey_F
        self.V_init = round(self.V_rev, 2)
        # Thermo-neutral voltage
        self.Vtn = self.ey_DH/self.ey_ne0/self.ey_F

        # Compute V_graph and Id for plots
        """
        if self.calc_Vgraph_Id:
            self.nn = int((self.ey_I_final - self.ey_I_initial) / self.ey_I_step)
            self.ey_I = [i for i in range(0, self.ey_I_final + 1, self.ey_I_step)]
            self.V_graph = [self.V_rev+(self.ey_r1+self.ey_r2*self.ey_T)*self.ey_I[i]/self.ey_A +
                            (self.ey_s1+self.ey_s2*self.ey_T+self.ey_s3*self.ey_T**2) *
                            log10((self.ey_t1+self.ey_t2/self.ey_T+self.ey_t3/self.ey_T**2) *
                                  self.ey_I[i]/self.ey_A+1) for i in range(int(self.nn) + 1)]
            self.Id = [i/2500 for i in self.ey_I]
        """
        if self.load_curve:
            # Fit the power curve input data
            self.p, self.timespan = fit_pdat(self.ey_pdat)

            # Compute the optimum number of Electrolyzers
            self.ey_Ne = ne_calc(join(base_path, self.ey_pdat), self.ey_E_size, self.ey_Ne)
        self.inc = 0

    def process_request(self, request):
        resp = self.ey_model(request)
        return resp

    def ey_model(self, req):
        resp = EYResponse()

        resp.ts = self.inc
        if self.load_curve:
            # Power profile (kW)
            resp.Pl = sum([self.p[j]*(resp.ts+1)**(21-j) for j in range(22)])
            # (W) to power one stack of electrolyzer
            resp.Pr = 1e3*resp.Pl/self.ey_Ne
        else:
            if self.inc == 0:
                self.ey_Ne = req/self.ey_E_size
                cprint("Electrolyzer size is: %d for P:%4.2f" % (self.ey_Ne, req), 'green')
            resp.Pr = 1e3 * req / self.ey_Ne

        resp.V, resp.Ir = fsolve(vi_calc, [self.ey_x01, self.ey_x02],
                                 args=(resp.Pr, self.ey_Nc, self.V_rev, self.ey_T,
                                       self.ey_r1, self.ey_r2, self.ey_s1, self.ey_s2,
                                       self.ey_s3, self.ey_t1, self.ey_t2, self.ey_t3,
                                       self.ey_A))
        resp.P = self.ey_Ne*self.ey_Nc*resp.V*resp.Ir

        # Compute Faraday Efficiency
        resp.nf = self.ey_a1*exp((self.ey_a2+self.ey_a3*self.ey_T+self.ey_a4*self.ey_T**2) /
                                 (resp.Ir/self.ey_A)+(self.ey_a5+self.ey_a6*self.ey_T+self.ey_a7*self.ey_T**2) /
                                 (resp.Ir/self.ey_A)**2)

        # Energy (or voltaje) efficiency of a cell
        resp.ne = self.Vtn/resp.V
        # Flow of H2 produced
        resp.Qh2_V = 80.69*self.ey_Nc*resp.Ir*resp.nf/2/self.ey_F       # (Nm^3/h)
        resp.Qh2_m = self.ey_Ne*self.ey_Nc*resp.Ir*resp.nf/2/self.ey_F  # (mol/s)
        resp.m_dotH2 = resp.Qh2_m*1e-3

        # Compressor model
        resp.P_tank = self.moles*self.ey_R*(self.ey_T+273.15)/self.ey_V_tank
        resp.Tout = (self.ey_T+273.15)*(resp.P_tank/self.ey_Pe)**((self.ey_gamma-1)/self.ey_gamma)
        resp.W_c = (resp.m_dotH2/self.ey_eta_c)*self.ey_cpH2*(resp.Tout-(self.ey_T+273.15))  # (kW)
        resp.P_tot = resp.W_c*1e3+resp.P

        # Storage Tank
        # Number of moles in time i in the tank
        self.moles = self.moles+resp.Qh2_m*1/self.ey_Nt
        resp.moles = self.moles
        resp.soc = resp.P_tank
        resp.soc_per = resp.soc/self.max_charge*100
        resp.isAvail = True
        if resp.soc >= self.max_charge:
            cprint('Charge time:' + '\t' * 7 + '%dsec.' % self.inc, 'green')
            soc_i = round((resp.soc/self.max_charge * 100), 1)
            cprint('State of Charge:' + '\t' * 6 + '%d%%' % soc_i, 'green')
            cprint('Tank is fully charged!!', 'cyan')
            resp.isAvail = False
        self.inc += 1
        return resp
