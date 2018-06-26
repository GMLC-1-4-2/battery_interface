# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from fleet_response import FleetResponse


class FleetInterface:
    """
    This class is base class for all services
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        pass

    def process_request(self, fleet_request):
        """
        Request for timestep ts

        :param fleet_request: an instance of FleetRequest
        :return fleet_response: an instance of FleetResponse
        """
        fleet_response = FleetResponse()
        fleet_response2 = FleetResponse()
		
        return fleet_response

    def forecast(self, fleet_requests):
        """
        Request for current time step

        :param requests: list of FleetRequest instances
        :return res: list of FleetResponse instances
        """
        fleet_responses = []
        for fleet_request in fleet_requests:
            fleet_response = FleetResponse()
            fleet_responses.append(fleet_response)

        return fleet_responses

    def change_config(self, **kwargs):
        """
        This function is here for future use. The idea of having it is for a service to communicate with a fleet
        in a nondeterministic manner during a simulation

        :param fleet_config: an instance of FleetConfig

        Example: Some fleets can operate in an autonomous mode, where they're not responding to requests,
        but watching, say, the voltage. If the voltage dips below some defined threshold (which a service might define),
        then the fleet responds in a pre-defined way.
        In this example, the kwargs can be {"voltage_threshold": new_value}
        """
        pass
