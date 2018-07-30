# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import unittest
from services.helpers.fleet_factory import FleetFactory
from fleets.battery_inverter_fleet.battery_inverter_fleet import BatteryInverterFleet

class TestFleetFactory(unittest.TestCase):

    def setUp(self):
        self.fleet_factory = FleetFactory()

    def test_instantiate_battery_inverter_fleet(self):

        fleet_name = "battery_inverter_fleet"
        fleet = self.fleet_factory.get_instance(fleet_name)
        self.assertIsInstance(fleet, BatteryInverterFleet)
