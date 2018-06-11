import sys
from datetime import datetime, timedelta
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from fleets.home_ac_fleet.home_ac_fleet import HomeAcFleet
from fleet_request import FleetRequest
from fleet_config import FleetConfig


if __name__ == '__main__':
    haf = HomeAcFleet()

    # Init simulation time frame
    start_time = datetime.utcnow()
    end_time = datetime.utcnow() + timedelta(hours=3)

    # Create requests for each hour in simulation time frame
    cur_time = start_time
    sim_time_step = timedelta(hours=1)
    fleet_requests = []
    while cur_time < end_time:
        req = FleetRequest(ts=cur_time, sim_step=sim_time_step, p=1000, q=1000)
        fleet_requests.append(req)
        cur_time += sim_time_step

    # Use case 1
    res = haf.process_request(fleet_requests[0])
    print(res)

    # Use case 2
    forecast = haf.forecast(fleet_requests)
    print(forecast)

    # Use case 3
    fleet_config = FleetConfig(is_P_priority=True, is_autonomous=False, autonomous_threshold=0.1)
    haf.change_config(fleet_config)
