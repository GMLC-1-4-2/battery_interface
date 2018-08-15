# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling a fleet of water heaters
@author: chuck booten, jeff maguire, xin jin
"""

import numpy as np
import os
import random

# this is the actual water heater model
from wh import WaterHeater

from WHFleet_Response import FleetResponse

class WaterHeaterFleet():
    def __init__(self, Steps = 100, Timestep = 60, P_request = 0, Q_request = 0, forecast = 0, StartHr = 40):
        self.numWH = 10 #number of water heaters to be simulated to represent the entire fleet
        self.Fleet_size_represented = max(self.numWH, 1e5)#size of the fleet that is represented by self.numWH
#        addshedTimestep NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 0.1, 0.2, 0.5, 1,2,3,4,5,6,10,12,15,20,30, 60, etc.
        self.MaxNumAnnualConditions = 20 #max # of annual conditions to calculate, if more WHs than this just reuse some of the conditions and water draw profiles
        self.TtankInitialMean = 123 #deg F
        self.TtankInitialStddev = 9.7 #deg F
        self.TsetInitialMean = 123 #deg F
        self.TsetInitialStddev = 9.7 #deg F
        self.minSOC = 0.2 # minimum SoC for aggregator to call for shed service
        self.maxSOC = 0.8 # minimum SoC for aggregator to call for add service
        self.minCapacityAdd = 350 #W-hr, minimum add capacity to be eligible for add service
        self.minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
        
        # for capacity, type, location and max. number of service calls need to specify discrete values and randomly sample to get a desired distribution 
        self.CapacityMasterList = [50,50,50,50,50,50,50,50,40,40,80] #70% 50 gal, 20% 40 gal, 10% 80 gal
        self.TypeMasterList = ['ER','ER','ER','ER','ER','ER','ER','ER','ER','HP'] #elec_resis 90% and HPWH 10%
        self.LocationMasterList =['living','living','living','living','unfinished basement'] #80% living, 20% unfinished basement for now
        self.MaxServiceCallMasterList = [100,80,80, 200, 150, 110, 50, 75, 100] # this is the max number of annual service calls for load add/shed.
        
    def process_request(self, ServiceRequest):
        
        response = ExecuteFleet()
        
        return response
        
    def ExecuteFleet(self, ServiceRequest): #Steps, Timestep, P_request, Q_request, forecast, StartHr
        
    
       ############################################################################# 
    #    generate distribution of initial WH fleet states. this means Ttank, Tset, capacity, location (cond/uncond), type (elec resis or HPWH).
    #    autogenerate water draw profile for the yr for each WH in fleet, this will be imported later, just get something reasonable here
        TsetInitial = np.random.normal(self.TsetInitialMean, self.TsetInitialStddev,self.numWH)
        TtankInitial = np.random.normal(self.TsetInitialMean, self.TsetInitialStddev,self.numWH)
        for x in range(self.numWH):
            TsetInitial[x] = max(TsetInitial[x],110)
            if TtankInitial[x] > TsetInitial[x]:
                TtankInitial[x] = TsetInitial[x]

        Capacity = [random.choice(self.CapacityMasterList) for n in range(self.numWH)]
#        Capacity_fleet_ave = sum(Capacity)/self.numWH
        Type = [random.choice(self.TypeMasterList) for n in range(self.numWH)]
        Location = [random.choice(self.LocationMasterList) for n in range(self.numWH)]
        MaxServiceCalls = [random.choice(self.MaxServiceCallMasterList) for n in range(self.numWH)]
        
        
        #for calculating annual conditions
        climate_location = 'Denver' # only allowable climate for now since the pre-run water draw profile generator has only been run for this climate
    #    10 different profiles for each number of bedrooms
    #    bedrooms can be 1-5
    #    gives 50 different draw profiles
    #    can shift profiles by 0-364 days
    #    gives 365*50 = 18250 different water draw profiles for each climate
        Tamb = []
        RHamb = []
        Tmains = []
        hot_draw =[]
        mixed_draw = []
        draw = []
        for a in range(self.numWH):             
            if a <= (self.MaxNumAnnualConditions-1): #if self.numWH > MaxNumAnnualConditions just start reusing older conditions to save computational time
                numbeds = random.randint(1, 5) 
                shift = random.randint(0, 364)
                unit = random.randint(0, 9)
                (tamb, rhamb, tmains, hotdraw, mixeddraw) = get_annual_conditions(climate_location,  Location[a], shift, numbeds, unit, ServiceRequest.Timestep, ServiceRequest.Steps, ServiceRequest.StartTime)
    #            print('tamb',tamb)
        
                Tamb.append(tamb)#have a Tamb for each step for each water heater being simulated 
                RHamb.append(rhamb)
                Tmains.append(tmains)
                hot_draw.append(hotdraw)
                mixed_draw.append(mixeddraw)
                draw.append(hotdraw + 0.3 * mixeddraw)#0.3 is so you don't need to know the exact hot/cold mixture for mixed draws, just assume 1/2 is hot and 1/2 is cold
    #            print('len Tamb',len(Tamb[0]))
    
            else: #start re-using conditions
                Tamb.append(Tamb[a % self.MaxNumAnnualConditions][:])
                RHamb.append(RHamb[a % self.MaxNumAnnualConditions][:])
                Tmains.append(Tmains[a % self.MaxNumAnnualConditions][:])
                hot_draw.append(hot_draw[a % self.MaxNumAnnualConditions][:])
                mixed_draw.append(mixed_draw[a % self.MaxNumAnnualConditions][:])
                draw.append(hot_draw[a-self.MaxNumAnnualConditions][:] + 0.3 * mixed_draw[a-self.MaxNumAnnualConditions][:])
#        print('len Tamb',len(Tamb[0]), len(Tamb))
#        print('len hotdraw',len(hot_draw[0]), len(hot_draw))
    #    print('Tamb',Tamb)
        draw_fleet = sum(draw)# this sums all rows, where each row is a WH, so gives the fleet sum of hot draw at each step
        draw_fleet_ave = draw_fleet/self.numWH  # this averages all rows, where each row is a WH, so gives the fleet average of hot draw at each step
#        print(len(draw_fleet_ave[0]),len(draw_fleet_ave))
       
    #    plt.figure(19)
    #    plt.clf()
    ##    plt.plot(hot_draw_fleet[0:200], 'k<-', label = 'hot')
    #    plt.plot(draw_fleet_ave[0:200], 'ro-',label = 'ave draw')
    #    plt.ylabel('Hot draw fleet [gal/step]')
    #    plt.legend()
    #    plt.xlabel('step')
    
        ###########################################################################  
        TotalServiceProvidedPerTimeStep = [0 for y in range(ServiceRequest.Steps)]
        TotalServiceCallsAcceptedPerWH = [0 for y in range(self.numWH)]
        
        SoCInit = [0 for y in range(self.numWH)]
        AvailableCapacityAddInit = [0 for y in range(self.numWH)]
        AvailableCapacityShedInit = [0 for y in range(self.numWH)]
        IsAvailableAddInit = [0 for y in range(self.numWH)]
        IsAvailableShedInit = [0 for y in range(self.numWH)]
    
        ##################################
        
    
    #    Initializing the water heater models
        whs = [WaterHeater(Tamb[0], RHamb[0], Tmains[0], 0, ServiceRequest.P_request, Capacity[number], Type[number], Location[number], 0, MaxServiceCalls[number]) for number in range(self.numWH)]
        FleetResponse.P_service = 0
        FleetResponse.P_service_max = 0
        FleetResponse.P_togrid = 0
        FleetResponse.P_togrid_max = 0
        FleetResponse.P_togrid_min = 0
        FleetResponse.P_forecast = 0
        FleetResponse.E = 0
        FleetResponse.C = 0
#        print(type(ServiceRequest.P_request))
        P_request_perWH = ServiceRequest.P_request[0] / self.numWH # this is only for the first step
        
        FleetResponse.Q_togrid = 0
        FleetResponse.Q_service = 0
        FleetResponse.Q_service_max = 0
        FleetResponse.Q_togrid_max = 0
        FleetResponse.Q_togrid_min = 0
        Eloss = 0
        Edel = 0
        
        TotalServiceCallsAcceptedPerWH = 0 * range(self.numWH)
        # run through fleet once as a forecast just to get initial conditions
        number = 0
        for w in whs:
            fcst = 1 #setting the forecast to 1 for this initialization only
#            ttank, tset, SoCInit, AvailableCapacityAddInit, AvailableCapacityShedInit, ServiceCallsAcceptedInit, eservice, IsAvailableAddInit, IsAvailableShedInit, elementon, eused, pusedmax
            response = w.execute(TtankInitial[number], TsetInitial[number], Tamb[number][0], RHamb[number][0], Tmains[number][0], draw[number][0], P_request_perWH, Type, ServiceRequest.Timestep, draw_fleet_ave[0], fcst) #forecast = 1
            number += 1
           
        for step in range(ServiceRequest.Steps):    
            number = 0
            servsum = 0
            NumDevicesToCall = 0
            laststep = step - 1
            P_request_perWH = ServiceRequest.P_request[step] / max(NumDevicesToCall,1)

#            decision making about which WH to call on for service, check if available at last step, if so then 
#            check for SoC > self.minSOC and Soc < self.maxSOC, whatever number that is, divide the total needed and ask for that for each
#            decided to add max and min SoC limits just in case, they might not matter but wanted limits other than just whether a device was available 
#            at the last timestep
            if step == 0: #use the initialized values to determine how many devices are available
                for n in range(self.numWH):
                    if P_request_perWH > 0 and IsAvailableAddInit[n] > 0 and SoCInit[n] < self.maxSOC and AvailableCapacityAddInit[n] > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perWH < 0 and IsAvailableShedInit[n] > 0 and SoCInit[n] > self.minSOC and AvailableCapacityShedInit[n] > self.minCapacityShed:
                        NumDevicesToCall += 1
            elif step > 0:
                for n in range(self.numWH):
                    if P_request_perWH > 0 and response.AvailableCapacityAdd > 0 and response.SOC < self.maxSOC and response.AvailableCapacityAdd > self.minCapacityAdd:
                        NumDevicesToCall += 1
                    elif P_request_perWH < 0 and response.AvailableCapacityShed > 0 and response.SOC > self.minSOC and response.AvailableCapacityShed > self.minCapacityShed:
                        NumDevicesToCall += 1          
        
        
            for wh in whs: #loop through water heatesr
                if step == 0: #ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailableAdd, isAvailableShed, elementon, eused, pusedmax
                    response = wh.execute(TtankInitial[number], TsetInitial[number], Tamb[number][0], RHamb[number][0], Tmains[number][0], draw[number][0], P_request_perWH, Type, ServiceRequest.Timestep, draw_fleet_ave[0], ServiceRequest.Forecast)
                else:
                    TsetLast = response.Tset
                    TtankLast = response.Ttank 
                    response = wh.execute(TtankLast, TsetLast, Tamb[number][step], RHamb[number][step], Tmains[number][step], draw[number][step], P_request_perWH, Type, ServiceRequest.Timestep, draw_fleet_ave[min([step,ServiceRequest.Steps-1])], ServiceRequest.Forecast) #min([step,ServiceRequest.Steps-1]) is to provide a forecast for the average fleet water draw for the next timestep while basically ignoring the last timestep forecast

                servsum += response.Eservice
                #FleetResponse.TotalServiceProvidedPerWH[number] = TotalServiceProvidedPerWH[number] + ServiceProvided[number][step]
                Eloss += response.Eloss
                Edel += response.Edel
                FleetResponse.P_togrid += response.Eused
                FleetResponse.P_togrid_max += response.PusedMax
                FleetResponse.P_togrid_min += response.PusedMin
                number += 1

                # Available Energy stored at the end of the most recent timestep (kWh)
                FleetResponse.E += response.Estored
                FleetResponse.C += response.SOC / (self.numWH)
                FleetResponse.P_service_max += response.AvailableCapacityShed # NOTE THIS ASSUMES THE MAX SERVICE IS LOAD SHED, DOES NOT CONSIDER LOAD ADD WHICH WILL BE DIFFERENT
                
            FleetResponse.P_dot_up = FleetResponse.P_togrid_max / ServiceRequest.Timestep.seconds
            FleetResponse.P_dot_down = FleetResponse.P_togrid / ServiceRequest.Timestep.seconds
            FleetResponse.P_service_min  = 0
            FleetResponse.Q_dot_up       = 0
            FleetResponse.Q_dot_down     = 0
            FleetResponse.dT_hold_limit  = None
            FleetResponse.T_restore      = None
            FleetResponse.Strike_price   = None
            FleetResponse.SOC_cost       = None
                
            TotalServiceProvidedPerTimeStep[step] += servsum
            if FleetResponse.P_togrid > 0:
                FleetResponse.Eff_charge = (FleetResponse.P_togrid - Eloss)/(FleetResponse.P_togrid)
            else:
                FleetResponse.Eff_charge = 0
            FleetResponse.Eff_discharge = (Edel)/(Edel + Eloss)
            
        if ServiceRequest.Forecast == 1:
            FleetResponse.P_forecast = FleetResponse.P_service
        else:
            FleetResponse.P_forecast = 0
    
        return FleetResponse
    
    ###########################################################################
    
    
def get_annual_conditions(climate_location, installation_location, days_shift, n_br,unit, timestep_min, num_steps, start_time):
    #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
    
    #Decompose utc timestamp to get the starting hour
    startmonthindex = [[1,0],[2,31],[3,59],[4,90],[5,120],[6,151],[7,181],[8,212],[9,243],[10,273],[11,304],[12,334]]
    start_month = start_time.month
    start_day = start_time.day
    start_hour = start_time.hour
    for m in startmonthindex:
        if start_month == m[0]:
            start_day += m[1]
            break
    start_hr = (start_day-1) * 24. + start_hour
    
    timestep_min = timestep_min.seconds / 60.
    num_steps_per_hr = int(np.ceil((60./float(timestep_min))))# how many hourly steps do you need to take if timestep is in minutes
    num_hrs = int(np.ceil(float(num_steps) / float(num_steps_per_hr)))
    num_mins = int(np.ceil(float(num_steps) * float(timestep_min )))
#        print('num_mins',num_mins)
    steps_per_min = int(np.ceil(1./float(timestep_min)))
    Tamb = []
    RHamb = []
    Tmains = []
    if climate_location != 'Denver':
        raise NameError("Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
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
        raise NameError("Error! Only allowed installation locations are living, unfinished basement, garage, unfinished attic. Change the installation location to a valid location")
    mains_temp_column = 9
    
    linenum = 0
    
    ambient_cond_file = open((os.path.join(os.path.dirname(__file__),'data_files','denver_conditions.csv')),'r') #hourly ambient air temperature and RH
    for line in ambient_cond_file:
        if linenum > start_hr and linenum <= (start_hr + num_hrs): #skip header all the way to the start hour but only go as many steps as are needed
            items = line.strip().split(',')
            for b in range(min(num_steps_per_hr,num_steps)): #repeat for however many steps there are in an hr
                Tamb.append([float(items[amb_temp_column])])
                RHamb.append([float(items[amb_rh_column])])
                Tmains.append([float(items[mains_temp_column])])
                b += 1
        linenum += 1
    ambient_cond_file.close()
    
    
    #Read in max and average values for the draw profiles
    linenum = 0
    n_beds = 0
    n_unit = 0
    
    #Total gal/day draw numbers based on BA HSP
    sh_hsp_tot = 14.0 + 4.67 * float(n_br)
    s_hsp_tot = 12.5 + 4.16 * float(n_br)
    cw_hsp_tot = 2.35 + 0.78 * float(n_br)
    dw_hsp_tot = 2.26 + 0.75 * float(n_br)
    b_hsp_tot = 3.50 + 1.17 * float(n_br)
    
    sh_max = np.zeros((5,10))
    s_max = np.zeros((5,10))
    b_max = np.zeros((5,10))
    cw_max = np.zeros((5,10))
    dw_max = np.zeros((5,10))
    sh_sum = np.zeros((5,10))
    s_sum = np.zeros((5,10))
    b_sum = np.zeros((5,10))
    cw_sum = np.zeros((5,10))
    dw_sum = np.zeros((5,10))
    
    sum_max_flows_file = open((os.path.join(os.path.dirname(__file__),'data_files', 'DrawProfiles','MinuteDrawProfilesMaxFlows.csv')),'r') #sum and max flows for all units and # of bedrooms
    for line in sum_max_flows_file:
        if linenum > 0: #this linenum is in min, not hours
            items = line.strip().split(',')
            n_beds = int(items[0]) - 1
            n_unit = int(items[1]) - 1
             #column is unit number, row is # of bedrooms. Taken directly from BEopt
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
    #Read in individual draw profiles
#    steps_per_year = int(np.ceil(60 * 24 * 365 / timestep_min))
    hot_draw = np.zeros((num_steps,1)) #steps_per_year
    mixed_draw = np.zeros((num_steps,1)) #steps_per_year
    #take into account days shifted
    draw_idx = 60 * 24 * days_shift
    if num_steps <= draw_idx: # if there aren't enough steps being simulated to account for the offset period then just ignore it
        offset = 0
    else:
        offset = draw_idx
        
    draw_profile_file = open((os.path.join(os.path.dirname(__file__),'data_files','DrawProfiles','DHWDrawSchedule_{}bed_unit{}_1min_fraction.csv'.format(n_br,unit))),'r') #minutely draw profile (shower, sink, CW, DW, bath)
    agghotflow = 0.0
    aggmixflow = 0.0
    nbr = n_br - 1 #go back to starting index at zero for python internal calcs
    for line in draw_profile_file:
        if linenum > start_hr*60 and linenum <= start_hr*60+ num_mins: #this linenum is in min
            
            items = line.strip().split(',')
            hot_flow = 0.0
            mixed_flow = 0.0
            
            if items[0] != '':
                sh_draw = float(items[0]) * sh_max[nbr,unit] * (sh_hsp_tot / sh_sum[nbr,unit])
                mixed_flow += sh_draw
            if items[1] != '':
                s_draw = float(items[1]) * s_max[nbr,unit] * (s_hsp_tot / s_sum[nbr,unit])
                mixed_flow += s_draw
            if items[2] != '':
                cw_draw = float(items[2]) * cw_max[nbr,unit] * (cw_hsp_tot / cw_sum[nbr,unit])
                hot_flow += cw_draw
            if items[3] != '':
                dw_draw = float(items[3]) * dw_max[nbr,unit] * (dw_hsp_tot / dw_sum[nbr,unit])
                hot_flow += dw_draw
            if items[4] != '':
                b_draw = float(items[4]) * b_max[nbr,unit] * (b_hsp_tot / b_sum[nbr,unit])
                mixed_flow += b_draw
            agghotflow += hot_flow
            aggmixflow += mixed_flow
#                aggregate whenever the linenum is a multiple of timestep_min. Each increment in lineum represents one minute. Timestep_min is the number of minutes per timestep
            if timestep_min >= 1: # aggregate if timesteps are >= 1 minute
                if linenum % timestep_min == 0: 
                    hot_draw[offset] = agghotflow
                    mixed_draw[offset] = aggmixflow
                    agghotflow = 0
                    aggmixflow = 0
                    draw_idx += 1
            elif timestep_min < 1: # repeat the value if timesteps are < 1 minute
#                    print('len draws',len(hot_draw))
#                    if linenum == 1:
#                        hot_draw[offset] = hot_flow #assume hot_draw = 0 up until draw_idx timestep
#                        mixed_draw[offset] = mixed_flow #assume mixed_draw = 0 up until draw_idx timestep
                    
                for c in range(min(steps_per_min,num_steps)): #repeat for however many steps there are in a minute 
#                        hot_draw = np.append(hot_draw,hot_flow)
#                        mixed_draw = np.append(mixed_draw,mixed_flow)
                    hot_draw[offset + c] = hot_flow #assume hot_draw = 0 up until draw_idx timestep
                    mixed_draw[offset + c] = mixed_flow
                    c += 1
#                    print('len hot_draw', len(hot_draw))    
        linenum += 1
#            if draw_idx >= steps_per_year:
#                draw_idx = 0
    draw_profile_file.close()
    return Tamb, RHamb, Tmains, hot_draw, mixed_draw
        
        
        
    


if __name__ == '__main__':
    main()