# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}


class FleetInterface:
    """
    This class is base class for all services
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        self.is_P_priority = True
        self.is_autonomous = False
        self.autonomous_threshold = None
        

    def process_request(self, ts, P_req, Q_req):
        """
        Request for timestep ts

        :param P_req:
        :param Q_req:

        :return res: an instance of FleetResponse
        print
        """
        from datetime import datetime, timedelta
        from fleet_request import FleetRequest
        req=FleetRequest(ts=datetime.utcnow(), sim_step=timedelta(hours=1),p=P_req, q=Q_req)
        
        from fleet_response import FleetResponse
        res=FleetResponse()
        
        import Fleet_PV
        
        Fleet_PV=Fleet_PV.Fleet(req.ts_req,req.sim_step,req.P_req,req.Q_req, False)
              
        res.P_togrid=Fleet_PV.P_grid
        res.Q_togrid=Fleet_PV.Q_grid
        res.P_service=Fleet_PV.P_service
        res.Q_service=Fleet_PV.P_service
        
        
        res.E              = Fleet_PV.E_t0
        res.C              = Fleet_PV.c
        res.P_togrid_max   = Fleet_PV.P_grid_max
        res.P_togrid_min   = Fleet_PV.P_grid_min
        res.Q_togrid_max   = Fleet_PV.Q_grid_max
        res.Q_togrid_min   = Fleet_PV.Q_grid_min
        res.P_service_max  = Fleet_PV.P_service_max
        res.P_service_min  = Fleet_PV.P_service_min
        res.Q_service_max  = Fleet_PV.Q_service_max
        res.Q_service_min  = Fleet_PV.Q_service_min
        res.P_dot_up       = Fleet_PV.NP_P_up
        res.P_dot_down     = Fleet_PV.NP_P_down
        res.Q_dot_up       = Fleet_PV.NP_Q_up
        res.Q_dot_down     = Fleet_PV.NP_Q_down
        res.Eff_charge     = Fleet_PV.NP_e_in
        res.Eff_discharge  = Fleet_PV.NP_e_out
        res.dT_hold_limit  = Fleet_PV.del_t_hold
        res.T_restore      = Fleet_PV.t_restore
        res.Strike_price   = Fleet_PV.SP
        res.SOC_cost       = None
        
        return res
        
#        from fleet_request import FleetRequest
#        req=FleetRequest(p=P_req,q=Q_req)
#        
#        from BEq_PV import BEq_PV
#        PV_fleet=BEq_PV
#        Fleet_PV=PV_fleet.service_response(req.P_req,req.Q_req,False)
#        print('P_grid = '+repr(Fleet_PV.P_grid))
#        
#        
#        from fleet_response import FleetResponse
#        PV_fleet_response=FleetResponse()
#        PV_fleet_response.P_injected=Fleet_PV.P_grid
#        print(PV_fleet_response.P_injected)
#        
#        return Fleet_PV.P_grid
        
        pass

    def forecast(self, requests):
        """
        Request for current timestep

        :param requests: list of  requests

        :return res: list of FleetResponse
        """
        from datetime import datetime, timedelta
        from fleet_request import FleetRequest
        req=FleetRequest(ts=datetime.utcnow(), sim_step=timedelta(hours=1),p=requests, q=[])
        
        from fleet_response import FleetResponse
        res=FleetResponse()
        
        import Fleet_PV
        
        Fleet_PV=Fleet_PV.Fleet(req.ts_req,req.sim_step,req.P_req,req.Q_req, True)
              
        res.P_togrid=[]
        res.Q_togrid=[]
        res.P_service=[]
        res.Q_service=[]
        
        
        res.E              = Fleet_PV.E_t0
        res.C              = Fleet_PV.c
        res.P_togrid_max   = Fleet_PV.P_grid_max
        res.P_togrid_min   = Fleet_PV.P_grid_min
        res.Q_togrid_max   = Fleet_PV.Q_grid_max
        res.Q_togrid_min   = Fleet_PV.Q_grid_min
        res.P_service_max  = Fleet_PV.P_service_max
        res.P_service_min  = Fleet_PV.P_service_min
        res.Q_service_max  = Fleet_PV.Q_service_max
        res.Q_service_min  = Fleet_PV.Q_service_min
        res.P_dot_up       = Fleet_PV.NP_P_up
        res.P_dot_down     = Fleet_PV.NP_P_down
        res.Q_dot_up       = Fleet_PV.NP_Q_up
        res.Q_dot_down     = Fleet_PV.NP_Q_down
        res.Eff_charge     = Fleet_PV.NP_e_in
        res.Eff_discharge  = Fleet_PV.NP_e_out
        res.dT_hold_limit  = Fleet_PV.del_t_hold
        res.T_restore      = Fleet_PV.t_restore
        res.Strike_price   = Fleet_PV.SP
        res.SOC_cost       = None
        
        return res

    def change_config(self, **kwargs):
        """
        This function is here for future use. The idea of having it is for a service to communicate with a fleet
        in a nondeterministic manner during a simulation

        :param kwargs: a dictionary of (key, value) pairs. The exact keys are decided by a fleet.

        Example: Some fleets can operate in an autonomous mode, where they're not responding to requests,
        but watching, say, the voltage. If the voltage dips below some defined threshold (which a service might define),
        then the fleet responds in a pre-defined way.
        In this example, the kwargs can be {"voltage_threshold": new_value}
        """
        pass
    
