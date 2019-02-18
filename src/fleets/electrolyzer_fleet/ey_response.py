# -*- coding: utf-8 -*-
# !/usr/bin/env python3
"""
@authors: rahul.kadavil@inl.gov, julian.ramirez@inl.gov,
"""


class EYResponse:
    """
    This class provides one time-step output for Electrolyzer based on time-series
    input power curve
    """
    def __init__(self):
        self.ts = 0
        self.Pl = 0
        self.Pr = 0
        self.V = 0
        self.Ir = 0
        self.P = 0
        self.nf = 0
        self.ne = 0
        self.Qh2_V = 0
        self.Qh2_m = 0
        self.m_dotH2 = 0
        self.P_tank = 0
        self.Tout = 0
        self.W_c = 0
        self.P_tot = 0
        self.moles = 0
        self.soc = 0
        self.soc_per = 0
        self.isAvail = True
