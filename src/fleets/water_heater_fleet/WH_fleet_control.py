# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling a fleet of water heaters
@author: chuck booten, jeff maguire, xin jin
"""

import numpy as np
import os
import random
import datetime
import csv

# this is the actual water heater model
from fleets.water_heater_fleet.wh import WaterHeater

from fleet_response import FleetResponse


class WaterHeaterFleet():
    def __init__(self, Steps=100, Timestep=60, P_request=0, Q_request=0, forecast=0, StartHr=40):
        self.numWH = 10  # number of water heaters to be simulated to represent the entire fleet
        self.Fleet_size_represented = max(self.numWH, 1e5)  # size of the fleet that is represented by self.numWH
        #        addshedTimestep NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 0.1, 0.2, 0.5, 1,2,3,4,5,6,10,12,15,20,30, 60, etc.
        self.MaxNumAnnualConditions = 20  # max # of annual conditions to calculate, if more WHs than this just reuse some of the conditions and water draw profiles
        self.TtankInitialMean = 123  # deg F
        self.TtankInitialStddev = 9.7  # deg F
        self.TsetInitialMean = 123  # deg F
        self.TsetInitialStddev = 9.7  # deg F
        self.minSOC = 0.2  # minimum SoC for aggregator to call for shed service
        self.maxSOC = 0.8  # minimum SoC for aggregator to call for add service
        self.minCapacityAdd = 350  # W-hr, minimum add capacity to be eligible for add service
        self.minCapacityShed = 150  # W-hr, minimum shed capacity to be eligible for shed service

        # for capacity, type, location and max. number of service calls need to specify discrete values and randomly sample to get a desired distribution
        self.CapacityMasterList = [50, 50, 50, 50, 50, 50, 50, 50, 40, 40, 80]  # 70% 50 gal, 20% 40 gal, 10% 80 gal
        self.TypeMasterList = ['ER', 'ER', 'ER', 'ER', 'ER', 'ER', 'ER', 'ER', 'ER',
                               'ER']  # all electric resistance until HPWHs can be modeled
        self.LocationMasterList = ['living', 'unfinished basement',
                                   'unfinished basement']  # 33% living, 67% unfinished basement
        self.MaxServiceCallMasterList = [100, 100, 100, 100, 100, 100, 100, 100,
                                         100]  # this is the max number of annual service calls for load add/shed.
        self.initializing_ts = True
        self.ts_idx = 0
        self.automated_response = False

    def process_request(self, ServiceRequest):

        response = self.ExecuteFleet(ServiceRequest)

        return response

    def ExecuteFleet(self, ServiceRequest):  # Steps, Timestep, P_request, Q_request, forecast, StartHr

        #############################################################################
        #    generate distribution of initial WH fleet states. this means Ttank, Tset, capacity, location (cond/uncond), type (elec resis or HPWH).
        #    autogenerate water draw profile for the yr for each WH in fleet, this will be imported later, just get something reasonable here
        if self.initializing_ts:
            self.TsetInitial = np.random.normal(self.TsetInitialMean, self.TsetInitialStddev, self.numWH)
            self.TtankInitial = np.random.normal(self.TsetInitialMean, self.TsetInitialStddev, self.numWH)
            for x in range(self.numWH):
                self.TsetInitial[x] = max(self.TsetInitial[x], 110)
                if self.TtankInitial[x] > self.TsetInitial[x]:
                    self.TtankInitial[x] = self.TsetInitial[x]

            self.Capacity = [random.choice(self.CapacityMasterList) for n in range(self.numWH)]
            #        Capacity_fleet_ave = sum(Capacity)/self.numWH
            self.Type = [random.choice(self.TypeMasterList) for n in range(self.numWH)]
            self.Location = [random.choice(self.LocationMasterList) for n in range(self.numWH)]
            self.MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numWH)]
            self.TsetLast = [0] * self.numWH
            self.TtankLast = [0] * self.numWH
            self.last_AvailableCapacityAdd = [0] * self.numWH
            self.SOC_last = [0] * self.numWH
            self.last_AvailableCapacityShed = [0] * self.numWH

            # for calculating annual conditions
            climate_location = 'Denver'  # only allowable climate for now since the pre-run water draw profile generator has only been run for this climate
            #    10 different profiles for each number of bedrooms
            #    bedrooms can be 1-5
            #    gives 50 different draw profiles
            #    can shift profiles by 0-364 days
            #    gives 365*50 = 18250 different water draw profiles for each climate
            self.Tamb = []
            self.RHamb = []
            self.Tmains = []
            self.hot_draw = []
            self.mixed_draw = []
            draw = []
            for a in range(self.numWH):
                if a <= (
                        self.MaxNumAnnualConditions - 1):  # if self.numWH > MaxNumAnnualConditions just start reusing older conditions to save computational time

                    # numbeds = random.randint(1, 5)
                    # shift = random.randint(0, 364)
                    # unit = random.randint(0, 9)
                    numbeds = 3
                    shift = 0
                    unit = 0
                    (tamb, rhamb, tmains, hotdraw, mixeddraw) = get_annual_conditions(climate_location,
                                                                                      self.Location[a], shift, numbeds,
                                                                                      unit, ServiceRequest.ts_req,
                                                                                      ServiceRequest.sim_step)

                    # First index is timestep, second is water heater
                    self.Tamb.append(tamb)  # have a Tamb for each step for each water heater being simulated
                    self.RHamb.append(rhamb)
                    self.Tmains.append(tmains)
                    self.hot_draw.append(hotdraw)
                    self.mixed_draw.append(mixeddraw)

                else:  # start re-using conditions
                    self.Tamb.append(self.Tamb[a % self.MaxNumAnnualConditions][:])
                    self.RHamb.append(self.RHamb[a % self.MaxNumAnnualConditions][:])
                    self.Tmains.append(self.Tmains[a % self.MaxNumAnnualConditions][:])
                    self.hot_draw.append(self.hot_draw[a % self.MaxNumAnnualConditions][:])
                    self.mixed_draw.append(self.mixed_draw[a % self.MaxNumAnnualConditions][:])

            #    plt.figure(19)
            #    plt.clf()
            #    plt.plot(hot_draw_fleet[0:200], 'k<-', label = 'hot')
            #    plt.plot(draw_fleet_ave[0:200], 'ro-',label = 'ave draw')
            #    plt.ylabel('Hot draw fleet [gal/step]')
            #    plt.legend()
            #    plt.xlabel('step')

            ###########################################################################
            TotalServiceProvidedPerTimeStep = [0]
            TotalServiceCallsAcceptedPerWH = [0 for y in range(self.numWH)]

            SoCInit = [0 for y in range(self.numWH)]
            AvailableCapacityAddInit = [0 for y in range(self.numWH)]
            AvailableCapacityShedInit = [0 for y in range(self.numWH)]
            IsAvailableAddInit = [0 for y in range(self.numWH)]
            IsAvailableShedInit = [0 for y in range(self.numWH)]

            ##################################

            #    Initializing the water heater models
            whs = [
                WaterHeater(self.Tamb[0], self.RHamb[0], self.Tmains[0], 0, ServiceRequest.P_req, self.Capacity[number],
                            self.Type[number], self.Location[number], ServiceRequest.ts_req,
                            self.MaxServiceCalls[number]) for number in range(self.numWH)]
            FleetResponse.P_service = 0
            FleetResponse.P_service_max = 0
            FleetResponse.P_togrid = 0
            FleetResponse.P_togrid_max = 0
            FleetResponse.P_togrid_min = 0
            FleetResponse.P_forecast = 0
            FleetResponse.E = 0
            FleetResponse.C = 0
            #        print(type(ServiceRequest.P_request))
            P_request_perWH = ServiceRequest.P_req / self.numWH  # this is only for the first step

            #TotalServiceCallsAcceptedPerWH = 0 * range(self.numWH)
            # run through fleet once as a forecast just to get initial conditions
            number = 0
            for w in whs:
                fcst = 1  # setting the forecast to 1 for this initialization only
                response = w.execute(self.TtankInitial[number], self.TsetInitial[number], self.Tamb[number][0],
                                     self.RHamb[number][0], self.Tmains[number][0], self.hot_draw[number][0],
                                     self.mixed_draw[number][0], P_request_perWH, self.Type, ServiceRequest.sim_step,
                                     fcst)
                number += 1

        else:
            fcst = 0
            number = 0
            whs = [WaterHeater(self.Tamb[number][self.ts_idx], self.RHamb[number][self.ts_idx],
                               self.Tmains[number][self.ts_idx], self.hot_draw[number][self.ts_idx],
                               ServiceRequest.P_req, self.Capacity[number], self.Type[number], self.Location[number],
                               ServiceRequest.ts_req, self.MaxServiceCalls[number]) for number in range(self.numWH)]
            # for step in range(ServiceRequest.Steps):

        number = 0
        FleetResponse.Q_togrid = 0
        FleetResponse.Q_service = 0
        FleetResponse.Q_service_max = 0
        FleetResponse.Q_togrid_max = 0
        FleetResponse.Q_togrid_min = 0
        Eloss = 0
        Edel = 0

        servsum = 0
        NumDevicesToCall = 0
        P_request_perWH = ServiceRequest.P_req / max(NumDevicesToCall, 1)

        #            decision making about which WH to call on for service, check if available at last step, if so then
        #            check for SoC > self.minSOC and Soc < self.maxSOC, whatever number that is, divide the total needed and ask for that for each
        #            decided to add max and min SoC limits just in case, they might not matter but wanted limits other than just whether a device was available
        #            at the last timestep
        if self.initializing_ts == True:  # use the initialized values to determine how many devices are available
            # Create the .csv file for the outputs from each WH
            outputfilename = "C:/Users/jmaguire/Desktop/WH_outputs/WH_fleet_outputs.csv"
            self.outputfile = open(outputfilename, "w")
            self.outputfile.write("Timestep,")
            for n in range(self.numWH):
                self.outputfile.write(
                    "Ttank_{},".format(n) + "Tset_{},".format(n) + "Eused_{},".format(n) + "PusedMax_{},".format(
                        n) + "Eloss_{},".format(n) + "ElementOn_{},".format(n) + "Eservice_{},".format(
                        n) + "SOC_{},".format(n) + "AvailableCapAdd_{},".format(n) + "AvailableCapShed_{},".format(
                        n) + "CallsAccepted_{},".format(n) + "AvailableAdd_{},".format(n) + "AvailableShed_{},".format(
                        n) + "Hot+MixedDrawVolume_{},".format(n) + "Edel_{},".format(n))
                if P_request_perWH > 0 and IsAvailableAddInit[n] > 0 and SoCInit[n] < self.maxSOC and \
                        AvailableCapacityAddInit[n] > self.minCapacityAdd:
                    NumDevicesToCall += 1
                elif P_request_perWH < 0 and IsAvailableShedInit[n] > 0 and SoCInit[n] > self.minSOC and \
                        AvailableCapacityShedInit[n] > self.minCapacityShed:
                    NumDevicesToCall += 1
            self.outputfile.write("\n")
        else:
            for n in range(self.numWH):
                if P_request_perWH > 0 and self.last_AvailableCapacityAdd[n] > 0 and self.SOC_last[n] < self.maxSOC and \
                        self.last_AvailableCapacityAdd[n] > self.minCapacityAdd:
                    NumDevicesToCall += 1
                elif P_request_perWH < 0 and self.last_AvailableCapacityShed > 0 and self.SOC_last[
                    n] > self.minSOC and self.last_AvailableCapacityShed > self.minCapacityShed:
                    NumDevicesToCall += 1

        self.outputfile.write("{},".format(ServiceRequest.ts_req))
        for wh in whs:  # loop through water heatesr
            if self.initializing_ts == True:  # ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailableAdd, isAvailableShed, elementon, eused, pusedmax
                response = wh.execute(self.TtankInitial[number], self.TsetInitial[number], self.Tamb[number][0],
                                      self.RHamb[number][0], self.Tmains[number][0], self.hot_draw[number][0],
                                      self.mixed_draw[number][0], P_request_perWH, self.Type, ServiceRequest.sim_step,
                                      fcst)
            else:
                response = wh.execute(self.TtankLast[number], self.TsetLast[number], self.Tamb[number][self.ts_idx],
                                      self.RHamb[number][self.ts_idx], self.Tmains[number][self.ts_idx],
                                      self.hot_draw[number][self.ts_idx], self.mixed_draw[number][self.ts_idx],
                                      P_request_perWH, self.Type, ServiceRequest.sim_step,
                                      fcst)  # min([step,ServiceRequest.Steps-1]) is to provide a forecast for the average fleet water draw for the next timestep while basically ignoring the last timestep forecast
            #                                                                         Ttank             Tset           Eused        PusedMax           Eloss        ElementOn          Eservice            SOC            AvailableCapAdd             AvailableCapShed                CallsAccepted              AvailableAdd             AvailableShed                                    Hot+ mixed DrawVolume                                Edel
            self.outputfile.write(
                "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},".format(response.Ttank, response.Tset, response.Eused,
                                                                       response.PusedMax, response.Eloss,
                                                                       response.ElementOn, response.Eservice,
                                                                       response.SOC, response.AvailableCapacityAdd,
                                                                       response.AvailableCapacityShed,
                                                                       response.ServiceCallsAccepted,
                                                                       response.IsAvailableAdd,
                                                                       response.IsAvailableShed,
                                                                       self.hot_draw[number][self.ts_idx] +
                                                                       self.mixed_draw[number][self.ts_idx],
                                                                       response.Edel))
            servsum += response.Eservice
            # FleetResponse.TotalServiceProvidedPerWH[number] = TotalServiceProvidedPerWH[number] + ServiceProvided[number][step]
            Eloss += response.Eloss
            Edel += response.Edel
            FleetResponse.P_togrid -= response.Eused
            FleetResponse.P_togrid_max -= response.PusedMax
            FleetResponse.P_togrid_min -= response.PusedMin
            self.TsetLast[number] = response.Tset
            self.TtankLast[number] = response.Ttank
            self.last_AvailableCapacityAdd[number] = response.AvailableCapacityAdd
            self.SOC_last[number] = response.SOC
            self.last_AvailableCapacityShed[number] = response.AvailableCapacityShed
            number += 1

            # Available Energy stored at the end of the most recent timestep (kWh)
            FleetResponse.E -= response.Estored
            FleetResponse.C -= response.SOC / (self.numWH)
            FleetResponse.P_service_max -= response.AvailableCapacityShed  # NOTE THIS ASSUMES THE MAX SERVICE IS LOAD SHED, DOES NOT CONSIDER LOAD ADD WHICH WILL BE DIFFERENT

        self.outputfile.write("\n")
        self.ts_idx += 1

        FleetResponse.P_dot_up = FleetResponse.P_togrid_max / ServiceRequest.sim_step.seconds
        FleetResponse.P_dot_down = FleetResponse.P_togrid / ServiceRequest.sim_step.seconds
        FleetResponse.P_service_min = 0
        FleetResponse.Q_dot_up = 0
        FleetResponse.Q_dot_down = 0
        FleetResponse.dT_hold_limit = None
        FleetResponse.T_restore = None
        FleetResponse.Strike_price = None
        FleetResponse.SOC_cost = None

        if FleetResponse.P_togrid > 0:
            FleetResponse.Eff_charge = (FleetResponse.P_togrid - Eloss) / (FleetResponse.P_togrid)
        else:
            FleetResponse.Eff_charge = 0
        FleetResponse.Eff_discharge = (Edel) / (Edel + Eloss)

        if fcst:
            FleetResponse.P_forecast = FleetResponse.P_service
        else:
            FleetResponse.P_forecast = 0

        self.initializing_ts = False
        return FleetResponse

    ###########################################################################


def get_annual_conditions(climate_location, installation_location, days_shift, n_br, unit, ts_req, sim_step):
    # reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use

    # Decompose utc timestamp to get the starting hour
    startmonthindex = [[1, 0], [2, 31], [3, 59], [4, 90], [5, 120], [6, 151], [7, 181], [8, 212], [9, 243], [10, 273],
                       [11, 304], [12, 334]]
    start_month = ts_req.month
    start_day = ts_req.day
    start_hour = ts_req.hour
    for m in startmonthindex:
        if start_month == m[0]:
            start_day += m[1]
            break
    start_hr = (start_day - 1) * 24. + start_hour
    hrs_left_yr = 8760 - start_hr
    timestep_min = sim_step.seconds / 60.
    num_steps_per_hr = int(
        np.ceil((60. / float(timestep_min))))  # how many hourly steps do you need to take if timestep is in minutes

    #        print('num_mins',num_mins)
    steps_per_min = int(np.ceil(1. / float(timestep_min)))
    Tamb = []
    RHamb = []
    Tmains = []
    if climate_location != 'Denver':
        raise NameError(
            "Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
    if installation_location == 'living':
        amb_temp_column = 1
        amb_rh_column = 2
    elif installation_location == 'unfinished basement':
        amb_temp_column = 3
        amb_rh_column = 4
    elif installation_location == 'garage':
        amb_temp_column = 5
        amb_rh_column = 6
    elif installation_location == 'unifinished attic':
        amb_temp_column = 7
        amb_rh_column = 8
    else:
        raise NameError(
            "Error! Only allowed installation locations are living, unfinished basement, garage, unfinished attic. Change the installation location to a valid location")
    mains_temp_column = 9

    linenum = 0

    ambient_cond_file = open((os.path.join(os.path.dirname(__file__), 'data_files', 'denver_conditions.csv')),
                             'r')  # hourly ambient air temperature and RH
    for line in ambient_cond_file:
        if linenum > start_hr:
            items = line.strip().split(',')
            for b in range(num_steps_per_hr):  # repeat for however many steps there are in an hr
                Tamb.append(float(items[amb_temp_column]))
                RHamb.append(float(items[amb_rh_column]))
                Tmains.append(float(items[mains_temp_column]))
                b += 1
        linenum += 1
    ambient_cond_file.close()

    # Read in max and average values for the draw profiles
    linenum = 0
    n_beds = 0
    n_unit = 0

    # Total gal/day draw numbers based on BA HSP
    sh_hsp_tot = 14.0 + 4.67 * float(n_br)
    s_hsp_tot = 12.5 + 4.16 * float(n_br)
    cw_hsp_tot = 2.35 + 0.78 * float(n_br)
    dw_hsp_tot = 2.26 + 0.75 * float(n_br)
    b_hsp_tot = 3.50 + 1.17 * float(n_br)

    sh_max = np.zeros((5, 10))
    s_max = np.zeros((5, 10))
    b_max = np.zeros((5, 10))
    cw_max = np.zeros((5, 10))
    dw_max = np.zeros((5, 10))
    sh_sum = np.zeros((5, 10))
    s_sum = np.zeros((5, 10))
    b_sum = np.zeros((5, 10))
    cw_sum = np.zeros((5, 10))
    dw_sum = np.zeros((5, 10))

    sum_max_flows_file = open(
        (os.path.join(os.path.dirname(__file__), 'data_files', 'DrawProfiles', 'MinuteDrawProfilesMaxFlows.csv')),
        'r')  # sum and max flows for all units and # of bedrooms
    for line in sum_max_flows_file:
        if linenum > 0:  # this linenum is in min, not hours
            items = line.strip().split(',')
            n_beds = int(items[0]) - 1
            n_unit = int(items[1]) - 1
            # column is unit number, row is # of bedrooms. Taken directly from BEopt
            sh_max[n_beds, n_unit] = float(items[2])
            s_max[n_beds, n_unit] = float(items[3])
            b_max[n_beds, n_unit] = float(items[4])
            cw_max[n_beds, n_unit] = float(items[5])
            dw_max[n_beds, n_unit] = float(items[6])
            sh_sum[n_beds, n_unit] = float(items[7])
            s_sum[n_beds, n_unit] = float(items[8])
            b_sum[n_beds, n_unit] = float(items[9])
            cw_sum[n_beds, n_unit] = float(items[10])
            dw_sum[n_beds, n_unit] = float(items[11])
        linenum += 1
    sum_max_flows_file.close()

    linenum = 0
    # Read in individual draw profiles
    #    steps_per_year = int(np.ceil(60 * 24 * 365 / timestep_min))
    hot_draw = []  # steps_per_year
    mixed_draw = []  # steps_per_year
    # take into account days shifted
    draw_idx = 60 * 24 * days_shift
    if hrs_left_yr <= draw_idx:  # if there aren't enough steps being simulated to account for the offset period then just ignore it
        offset = 0
    else:
        offset = draw_idx

    draw_profile_file = open((os.path.join(os.path.dirname(__file__), 'data_files', 'DrawProfiles',
                                           'DHWDrawSchedule_{}bed_unit{}_1min_fraction.csv'.format(n_br, unit))),
                             'r')  # minutely draw profile (shower, sink, CW, DW, bath)
    agghotflow = 0.0
    aggmixflow = 0.0
    nbr = n_br - 1  # go back to starting index at zero for python internal calcs
    for line in draw_profile_file:
        if linenum > start_hr * 60:  # this linenum is in min
            items = line.strip().split(',')
            hot_flow = 0.0
            mixed_flow = 0.0
            agghotflow = 0.0
            aggmixflow = 0.0

            if items[0] != '':
                sh_draw = float(items[0]) * sh_max[nbr, unit] * (sh_hsp_tot / sh_sum[nbr, unit])
                mixed_flow += sh_draw
            if items[1] != '':
                s_draw = float(items[1]) * s_max[nbr, unit] * (s_hsp_tot / s_sum[nbr, unit])
                mixed_flow += s_draw
            if items[2] != '':
                cw_draw = float(items[2]) * cw_max[nbr, unit] * (cw_hsp_tot / cw_sum[nbr, unit])
                hot_flow += cw_draw
            if items[3] != '':
                dw_draw = float(items[3]) * dw_max[nbr, unit] * (dw_hsp_tot / dw_sum[nbr, unit])
                hot_flow += dw_draw
            if items[4] != '':
                b_draw = float(items[4]) * b_max[nbr, unit] * (b_hsp_tot / b_sum[nbr, unit])
                mixed_flow += b_draw
            agghotflow += hot_flow
            aggmixflow += mixed_flow

            hot_draw.append(agghotflow)
            mixed_draw.append(aggmixflow)
            '''
#                aggregate whenever the linenum is a multiple of timestep_min. Each increment in lineum represents one minute. Timestep_min is the number of minutes per timestep
            if timestep_min >= 1: # aggregate if timesteps are >= 1 minute
                if linenum % timestep_min == 0: 

                    agghotflow = 0
                    aggmixflow = 0
                    draw_idx += 1
            elif timestep_min < 1: # repeat the value if timesteps are < 1 minute                  
                for c in range(min(steps_per_min,hrs_left_yr)): #repeat for however many steps there are in a minute 
#                        hot_draw = np.append(hot_draw,hot_flow)
#                        mixed_draw = np.append(mixed_draw,mixed_flow)
                    hot_draw.append(hot_flow) #assume hot_draw = 0 up until draw_idx timestep
                    mixed_draw[offset + c] = mixed_flow
                    c += 1
#                    print('len hot_draw', len(hot_draw))    
            '''
        linenum += 1
    #            if draw_idx >= steps_per_year:
    #                draw_idx = 0
    draw_profile_file.close()
    return Tamb, RHamb, Tmains, hot_draw, mixed_draw


if __name__ == '__main__':
    main()