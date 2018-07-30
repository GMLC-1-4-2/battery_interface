import pandas as pd

class ClearingPriceHelper(object):

    def read_clearing_prices(self, input_data_file_path, local_day, local_hour):

        sheet_name = self._get_sheet_name(local_day)

        excel_data = pd.read_excel(input_data_file_path, sheet_name)
        #print("excel_data.head(): ", excel_data.head())
        #print("type(excel_data['LOCALDAY'][0])", type(excel_data['LOCALDAY'][0]))
        #print("type(excel_data['LOCALHOUR'])", type(excel_data['LOCALHOUR']))

        matching_row_data_frame = excel_data[(excel_data['LOCALDAY'] == local_day) & (excel_data['LOCALHOUR'] == int(local_hour)) & (excel_data['SERVICE'] == "REG")]
        matching_row_series = matching_row_data_frame.iloc[0]

        return {"MCP": matching_row_series['MCP'], "REG_CCP": matching_row_series['REG_CCP'], "REG_PCP": matching_row_series['REG_PCP']}

    def _get_sheet_name(self, local_day):
        timestamp = pd.Timestamp(local_day)
        return timestamp.strftime("%B_%Y")
