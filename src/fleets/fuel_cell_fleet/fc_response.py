# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""


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
