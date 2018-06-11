# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}


class FleetConfig:
    """
    This class describes input fields required by fleets
    """

    def __init__(self, is_P_priority=True, is_autonomous=False, autonomous_threshold=None):
        self.is_P_priority = is_P_priority
        self.is_autonomous = is_autonomous
        self.autonomous_threshold = autonomous_threshold
