import unittest
import os
from dateutil import parser
import numpy as np
from services.helpers.historial_signal_helper import HistoricalSignalHelper

class TestHistoricalSignalHelper(unittest.TestCase):

    def setUp(self):
        self.historial_signal_helper = HistoricalSignalHelper()

    def test_read_historial_signal_from_sheet(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-08-02 00:00:00")
        end_time = parser.parse("2017-08-02 00:00:10")

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures/files/08_2017_reduced_size.xlsx"))

        self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)
        actual_signals = self.historial_signal_helper.signals_in_range(start_time, end_time)

        #print("actual_signals: ", actual_signals)

        # expected_signals = np.array(['-0.49734288814011735', '-0.4978015549937998',
        #                              '-0.498587711999932', '-0.49966560301435453',
        #                              '-0.48042063823334713', '-0.4735139582609288'])
        expected_signals = np.array([-0.497343, -0.497802, -0.498588, -0.499666, -0.480421, -0.473514])

        #np.testing.assert_array_equal(actual_signals, expected_signals)
        np.testing.assert_allclose(actual_signals, expected_signals, rtol = 1e-6, atol = 0)
