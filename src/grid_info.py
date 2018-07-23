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
        self.__voltage = 1.0  # Private. Use get_voltage to get the value
        self.__frequency = 60.0  # Private. Use get_frequency to get the frequency

    def get_voltage(self, location):
        """
        To be changed later
        :param location:
        :return:
        """
        return self.__voltage

    def get_frequency(self, location):
        """
        To be changed later
        :param location:
        :return:
        """
        return self.__frequency
