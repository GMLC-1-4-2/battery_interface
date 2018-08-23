import unittest
import os
from dateutil import parser
import datetime
from services.trad_reg_service.helpers.historical_signal_helper import HistoricalSignalHelper
from services.exceptions.datetime_validation_exception import DatetimeValidationException

class TestHistoricalSignalHelper(unittest.TestCase):

    def setUp(self):
        self.historial_signal_helper = HistoricalSignalHelper()

    def test_get_historial_signal_in_range_within_the_same_day(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-08-02 00:00:00")
        end_time = parser.parse("2017-08-02 00:00:10")

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fixtures/files/08_2017_reduced_size.xlsx"))

        self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)
        actual_signals = self.historial_signal_helper.signals_in_range(start_time, end_time)

        #print("actual_signals: ", actual_signals)

        # expected_signals = np.array(['-0.49734288814011735', '-0.4978015549937998',
        #                              '-0.498587711999932', '-0.49966560301435453',
        #                              '-0.48042063823334713', '-0.4735139582609288'])
        #expected_signals = np.array([-0.497343, -0.497802, -0.498588, -0.499666, -0.480421, -0.473514])
        expected_signals = {datetime.datetime(2017, 8, 2, 0, 0): -0.49734288814011735,
                            datetime.datetime(2017, 8, 2, 0, 0, 2): -0.4978015549937998,
                            datetime.datetime(2017, 8, 2, 0, 0, 4): -0.498587711999932,
                            datetime.datetime(2017, 8, 2, 0, 0, 6): -0.49966560301435453,
                            datetime.datetime(2017, 8, 2, 0, 0, 8): -0.48042063823334713,
                            datetime.datetime(2017, 8, 2, 0, 0, 10): -0.4735139582609288}

        #np.testing.assert_array_equal(actual_signals, expected_signals)
        #np.testing.assert_allclose(actual_signals, expected_signals, rtol = 1e-6, atol = 0)
        self.assertEqual(actual_signals, expected_signals)

    def test_get_historial_signal_in_range_encompassing_multiple_days(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-08-03 23:59:54")
        end_time = parser.parse("2017-08-04 00:00:02")

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fixtures/files/08_2017_reduced_size.xlsx"))

        self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)
        actual_signals = self.historial_signal_helper.signals_in_range(start_time, end_time)

        expected_signals = {datetime.datetime(2017, 8, 3, 23, 59, 54): 0.2383686104732162,
                            datetime.datetime(2017, 8, 3, 23, 59, 56): 0.2371792581707951,
                            datetime.datetime(2017, 8, 3, 23, 59, 58): 0.23626120505479414,
                            datetime.datetime(2017, 8, 4, 0, 0, 0): 0.23557409084697634,
                            datetime.datetime(2017, 8, 4, 0, 0, 2): 0.23508375252473068}

        self.assertEqual(actual_signals, expected_signals)

    def test_start_time_after_end_time_should_raise_exception(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-08-01 04:00:00")
        end_time = parser.parse("2017-08-01 00:00:00")

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fixtures/files/08_2017_reduced_size.xlsx"))

        self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)

        with self.assertRaises(DatetimeValidationException) as context:
            self.historial_signal_helper.signals_in_range(start_time, end_time)

        self.assertTrue("Start time: 2017-08-01 04:00:00, End time: 2017-08-01 00:00:00. Start time must not be after end time." in str(context.exception))

    # def test_stat_time_and_end_time_not_in_same_month_should_raise_exception(self):
    #
    #     sheet_name = "Traditional"
    #     start_time = parser.parse("2017-08-31 23:00:00")
    #     end_time = parser.parse("2017-09-01 00:00:00")
    #
    #     input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fixtures/files/08_2017_reduced_size.xlsx"))
    #
    #     self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)
    #
    #     with self.assertRaises(DatetimeValidationException) as context:
    #         self.historial_signal_helper.signals_in_range(start_time, end_time)
    #
    #     self.assertTrue("Start time: year = 2017 month = 8, End time: year = 2017 month = 9. Start date and end date must be in the same month. Currently, range in multiple months is not supported." in str(context.exception))

    def test_start_time_and_end_time_in_previous_month_should_raise_exception(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-07-01 00:00:00")
        end_time = parser.parse("2017-07-01 04:00:00")

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fixtures/files/08_2017_reduced_size.xlsx"))

        self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)

        with self.assertRaises(DatetimeValidationException) as context:
            self.historial_signal_helper.signals_in_range(start_time, end_time)

        self.assertTrue("Start time: year = 2017 month = 7, End time: year = 2017 month = 7. Start time and end time must be within the date range of given data: between 2017-08-01 00:00:00 and 2017-08-10 23:59:58." in str(context.exception))

    def test_start_time_and_end_time_in_next_month_should_raise_exception(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-09-01 00:00:00")
        end_time = parser.parse("2017-09-01 04:00:00")

        input_data_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fixtures/files/08_2017_reduced_size.xlsx"))

        self.historial_signal_helper.read_and_store_historical_signals(input_data_file_path, sheet_name)

        with self.assertRaises(DatetimeValidationException) as context:
            self.historial_signal_helper.signals_in_range(start_time, end_time)

        self.assertTrue("Start time: year = 2017 month = 9, End time: year = 2017 month = 9. Start time and end time must be within the date range of given data: between 2017-08-01 00:00:00 and 2017-08-10 23:59:58." in str(context.exception))

    def test_infer_filename_from_datatime(self):

        sheet_name = "Traditional"
        start_time = parser.parse("2017-08-01 00:00:00")

        actual_filename = self.historial_signal_helper.get_input_filename(start_time)

        expected_filename = '08 2017.xlsx'

        self.assertEqual(actual_filename, expected_filename)

if __name__ == '__main__':
    unittest.main()
