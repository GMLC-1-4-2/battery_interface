# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
Description: This class implements the FuelCell FleetInterface to integrate with a fleet of
FuelCells
"""

from _load import *
from fleet_interface import FleetInterface
from fuel_cell_fleet.fc_response import FCResponse
from helpers import fit_pdat, vifc_calc, ne_calc
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
colorama.init()


class FuelCellFleet(FleetInterface):
    """
    FuelCell Fleet Class
    """

    def __init__(self, grid_info, mdl_config="config.ini", mdl_type="FuelCell", p_req=None, **kwargs):
        """
        :param GridInfo: GridInfo object derived from the GridInfo Class
        :param mdl_type: Default model parameter values
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
                cprint("FuelCell size is: %d for P:%4.2f" % (self.fc_Nfc, req), 'green')
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
