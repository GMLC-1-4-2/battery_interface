import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from services.peak_managment_service.peak_management_service import PeakManagementService


if __name__ == '__main__':
    pms = PeakManagementService()

    # Use case 1
    print(pms.request())

    # Use case 2
    print(pms.forecast())

    # Use case 3
    pms.change_config()
