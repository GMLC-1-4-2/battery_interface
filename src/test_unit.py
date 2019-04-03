import unittest

from dateutil import parser
from fleet_request import FleetRequest
from datetime import datetime, timedelta
from fleet_factory import create_fleet

# fleets = ['BatteryInverter', 'ElectricVehicle', 'PV', 'WaterHeater', 'Electrolyzer', 'FuelCell', 'HVAC', 'Refridge' ]
fleet_name = 'Electrolyzer'

#======================   DEVICE API TESTING   =============================

class TestDeviceAPI(unittest.TestCase):
# This class is specifically designed to test for the presense of device output consistent with the virtual battery API
# See Table 3.4 of the "Battery-Equivalent Models for Distributed Energy Resource Devices’ Ability to Provide
# Grid Services" Report

    def setUp(self):
    #This method instantiates the fleet and executes a simple request to get the device response for evaluation

        #start_time = parser.parse('8/1/17 16:00')
        #cur_time = parser.parse('8/1/17 16:00')
        #delt = timedelta(seconds=30)

        start_time = datetime.utcnow()
        cur_time = datetime.utcnow()
        delt = timedelta(hours=0.000277777778)

        Prequest = 10;
        Qrequest = None;

        kwargs = {}
        kwargs['start_time'] = start_time
        grid_type = 1

    # Create test fleet
        fleet = create_fleet(fleet_name, grid_type, **kwargs)
        if fleet is None:
            raise 'Could not create fleet with name ' + fleet_name

        fleet_request = FleetRequest(cur_time, delt, start_time, Prequest, Qrequest)
        fleet_response = fleet.process_request(fleet_request)
        self.response = fleet_response

    #Variables below are grid service request responses for the time period beginning at t0
    # and are returned to the high-level model

    def test_P_base(self):
        self.assertIsNotNone(self.response.P_base, 'P_base is not provided!')

    def test_P_togrid(self):
        self.assertIsNotNone(self.response.P_togrid, 'P_togrid is not provided!')

    def test_Q_togrid(self):
        self.assertIsNotNone(self.response.Q_togrid, 'Q_togrid is not provided!')

    def test_P_service(self):
        self.assertIsNotNone(self.response.P_service, 'P_service is not provided!')

    def test_Q_service(self):
        self.assertIsNotNone(self.response.Q_service, 'Q_service is not provided!')

    def test_E(self):
        self.assertIsNotNone(self.response.E, 'E (available energy stored) is not provided!')

    # Variables below are Battery-Equivalent API Constraint variables passed from the device fleet to
    # the high-level model for the next time step (t1)

    def test_C(self):
        self.assertIsNotNone(self.response.C, 'C (potential energy capacity) is not provided!')

    def test_P_togrid_max(self):
        self.assertIsNotNone(self.response.P_togrid_max, 'P_togrid_max is not provided!')

    def test_Q_togrid_max(self):
        self.assertIsNotNone(self.response.Q_togrid_max, 'Q_togrid_max is not provided!')

    def test_P_togrid_min(self):
        self.assertIsNotNone(self.response.P_togrid_min, 'P_togrid_min is not provided!')

    def test_Q_togrid_min(self):
        self.assertIsNotNone(self.response.Q_togrid_min, 'Q_togrid_min is not provided!')

    def test_P_service_max(self):
        self.assertIsNotNone(self.response.P_service_max, 'P_service_max is not provided!')

    def test_Q_service_max(self):
        self.assertIsNotNone(self.response.Q_service_max, 'Q_service_max is not provided!')

    def test_P_service_min(self):
        self.assertIsNotNone(self.response.P_service_min, 'P_service_min is not provided!')

    def test_Q_service_min(self):
        self.assertIsNotNone(self.response.Q_service_min, 'Q_service_min is not provided!')

    def test_P_dot_up(self):
        self.assertIsNotNone(self.response.P_dot_up, 'P_dot_up is not provided!')

    def test_Q_dot_up(self):
        self.assertIsNotNone(self.response.Q_dot_up, 'Q_dot_up is not provided!')

    def test_P_dot_down(self):
        self.assertIsNotNone(self.response.P_dot_down, 'P_dot_down is not provided!')

    def test_Q_service_min(self):
        self.assertIsNotNone(self.response.Q_dot_down, 'Q_dot_down is not provided!')

    def test_Eff_charge(self):
        self.assertIsNotNone(self.response.Eff_charge, 'Eff_charge is not provided!')

    def test_Eff_discharge(self):
        self.assertIsNotNone(self.response.Eff_discharge, 'Eff_discharge is not provided!')

    def test_dT_hold_limit(self):
        self.assertIsNotNone(self.response.dT_hold_limit, 'dT_hold_limit is not provided!')

    def test_T_restore(self):
        self.assertIsNotNone(self.response.T_restore, 'T_restore is not provided!')

    def test_Strike_price(self):
        self.assertIsNotNone(self.response.Strike_price, 'Strike_price is not provided!')

    def test_SOC_cost(self):
        self.assertIsNotNone(self.response.SOC_cost, 'SOC_cost is not provided!')

    def tearDown(self):
        self.response = []

#======================   DEVICE TIME MANAGEMENT TESTING   =============================

class TestDeviceTime(unittest.TestCase):
# This class is specifically designed to test for consistency and flexibility in handling timestampes and timesteps

    def setUp(self):
    #This method instantiates the fleet and executes a simple request to get the device response for evaluation

        start_time = parser.parse('8/1/17 16:00')
        #cur_time = parser.parse('8/1/17 16:00')
        cur_time = datetime.utcnow()
        delt = timedelta(seconds=0.5)

        Prequest = 10;
        Qrequest = None;

        kwargs = {}
        kwargs['start_time'] = start_time
        grid_type = 1

    # Create test fleet
        fleet = create_fleet(fleet_name, grid_type, **kwargs)
        if fleet is None:
            raise 'Could not create fleet with name ' + fleet_name

        fleet_request = FleetRequest(cur_time, delt, start_time, Prequest, Qrequest)
        fleet_response = fleet.process_request(fleet_request)
        self.response = fleet_response
        self.cur_time = cur_time
        self.delt = delt

    #Variables below are grid service request responses for the time period beginning at t0
    # and are returned to the high-level model

    def test_TimeStamp(self):
        self.assertEqual(self.response.ts, self.cur_time, 'Request and response timestamps do not match')

    def test_TimeStep(self):
        self.assertEqual(self.response.sim_step, self.delt, 'Request and response timesteps do not match')

    def tearDown(self):
        self.response = []



if __name__ == '__main__':
    unittest.main()

#Concepts for later tests:
# Evaluate that P-Service is reasonable and of the correct sign.
# Test to see that the devices can run with a range of P_request and Q_request
# Entire test class for frequency response. - skip test for fleets not eligible.
# Check that fleet passes scaling factor
# Run to see that it can run with range of start times.
# Run to see that it can run with range of time-steps.
# Investigate test class grouping to see if execution can be sped up by doing setup once per set of tests.
