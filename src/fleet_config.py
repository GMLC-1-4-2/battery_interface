# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}


class FleetConfig:
    """
    This class describes configurable parameters of a fleet
    """

    def __init__(self, is_P_priority=True, is_autonomous=False, f_thresholds=[], v_thresholds=[]):
        self.is_P_priority = is_P_priority
        self.is_autonomous = is_autonomous
        self.f_thresholds = f_thresholds
        self.v_thresholds = v_thresholds
