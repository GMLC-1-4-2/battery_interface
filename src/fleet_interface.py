# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from fleet_response import FleetResponse


class FleetInterface:
    """
    This class is base class for all fleets
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        # It represents the percentage of devices within the fleet that are available to provide grid services
        # It is a number between 0-1
        self.service_weight = 1
        # Maximum absolute power that the fleet is able to provide (kW)
        self.fleet_rating = 1000

    def process_request(self, fleet_request):
        """
        Request for timestep ts

        :param fleet_request: an instance of FleetRequest
        :return fleet_response: an instance of FleetResponse
        """
        fleet_response = FleetResponse()
        fleet_response.ts = fleet_request.ts_req
        fleet_response.P_service = fleet_request.P_req

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

    def change_config(self, fleet_config, **kwargs):
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

    def output_impact_metrics(self): 
        """
        This function exports the impact metrics of each sub fleet
        """
        pass        

    def assigned_service_kW(self):
        """ 
        This function allows weight and fleet rating to be passed to the service model. 
        Scale the service to the size of the fleet
        """
        return self.service_weight*self.fleet_rating

    def print_performance_info(self):
        """
        This function is to dump the performance metrics either to screen or file or both
        :return:
        """
        pass
