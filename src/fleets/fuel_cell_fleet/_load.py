# -*- coding: utf-8 -*-
# !/usr/bin/env python3
import sys
from os.path import dirname, abspath, join
from warnings import simplefilter, filterwarnings
try:
    import colorama
except ImportError:
    raise ImportError('colorama package missing!!')
try:
    from termcolor import cprint
except ImportError:
    raise ImportError('termcolor package missing!!')
try:
    import configparser
except ImportError:
    raise ImportError('configparser package missing!!')
try:
    from numpy import zeros, polyfit, convolve, RankWarning, trapz, log, log10, exp
except ImportError:
    raise ImportError('numpy package missing!!')
try:
    from scipy.optimize import fsolve
except ImportError:
    raise ImportError('scipy package missing!!')
try:
    from pandas import read_csv
except ImportError:
    raise ImportError('pandas package missing!!')
try:
    from matplotlib.pyplot import figure, subplot2grid, savefig
except ImportError:
    raise ImportError('matplotlib package missing!!')
