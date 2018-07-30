import unittest
import os
import pandas as pd
from services.helpers.clearing_price_helper import ClearingPriceHelper

class TestClearingPriceHelper(unittest.TestCase):

    def setUp(self):
        self.clearing_price_helper = ClearingPriceHelper()

    def test_read_clearing_price_from_sheet(self):

        #local_day = "01-AUG-2017"
        #local_hour = "00"
        sheet_name = "August_2017"

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures/files/historical-ancillary-service-data-2017.xls"))

        actual_clearing_prices = self.clearing_price_helper.read_and_store_clearing_prices(input_data_file_path, sheet_name)

        #print("actual_clearing_prices: ", actual_clearing_prices)

        #expected_clearing_prices = {"MCP": 9.870000000000001, "REG_CCP": 2.84, "REG_PCP": 7.03}
        expected_clearing_price_for_first_hour = [9.870000000000001, 2.84, 7.03]

        self.assertEqual(actual_clearing_prices[pd.Timestamp('2017-08-01 00:00:00')], expected_clearing_price_for_first_hour)
