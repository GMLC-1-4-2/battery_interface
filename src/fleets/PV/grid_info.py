# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 12:13:04 2018

@author: rmahmud
"""

# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from __future__ import absolute_import


class GridInfo:
    """
    This class provides common info about the grid
    """

    def __init__(self, *args, **kwargs):
        self.voltage = 1.0
        self.frequency = 60.0

    def get_voltage(self, location):
        return self.voltage

    def get_frequency(self, location):
        return self.frequency