import unittest
import os
from services.helpers.excel_helper import ExcelHelper


class TestExcelHelper(unittest.TestCase):

    def setUp(self):
        self.excel_helper = ExcelHelper()

    def test_read_from_sheet(self):

        local_day = "01-AUG-2017"
        local_hour = "00"

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures/files/historical-ancillary-service-data-2017.xls"))

        actual_clearing_prices = self.excel_helper.read_clearing_prices(input_data_file_path, local_day, local_hour)

        #print("actual_clearing_prices: ", actual_clearing_prices)

        expected_clearing_prices = {"MCP": 9.870000000000001, "REG_CCP": 2.84, "REG_PCP": 7.03}

        self.assertEqual(actual_clearing_prices, expected_clearing_prices)
