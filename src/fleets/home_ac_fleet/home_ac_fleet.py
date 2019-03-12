# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from fleet_interface import FleetInterface
from fleet_request import FleetRequest
from fleet_response import FleetResponse


class HomeAcFleet(FleetInterface):
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """

    def __init__(self, GridInfo, *args, **kwargs):
        # This set is a subset of FleetConfig
        self.is_P_priority = True
        self.is_autonomous = False
        self.autonomous_threshold = None
        self.grid_info = GridInfo

    def process_request(self, fleet_request):
        """
        The expectation that configuration will have at least the following
        items

        :param fleet_request: an instance of FleetRequest

        :return res: an instance of FleetResponse
        """

        res = FleetResponse()
        # Dummy values for testing
        res.P_togrid = 100
        res.P_service = 100
        res.Q_service = 100
        res.Q_togrid = 100

        return res

    def forecast(self, fleet_requests):
        """
        Forcast feature

        :param fleet_requests: list of service requests

        :return res: list of service responses
        """

        responses = []

        # Iterate and process each request in fleet_requests
        for req in fleet_requests:
            res = self.process_request(req)
            responses.append(res)

        return responses

    def change_config(self, fleet_config):
        """
        :param fleet_config: an instance of FleetConfig
        """
        self.is_P_priority = fleet_config.is_P_priority
        self.is_autonomous = fleet_config.is_autonomous
        self.autonomous_threshold = fleet_config.autonomous_threshold
