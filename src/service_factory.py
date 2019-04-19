def create_service(name, **kwargs):
    if name == 'Regulation':
        from services.reg_service.reg_service import RegService

        return RegService()

    elif name == 'ArtificialInertia':
        from services.artificial_inertia_service.artificial_inertia_service import ArtificialInertiaService
        return ArtificialInertiaService()

    elif name == 'Reserve':
        from services.reserve_service.reserve_service import ReserveService

        return ReserveService()
        
    elif name == 'DistributionVoltageService':
        from services.distribution_voltage_regulation.distribution_regulation_service import DistributionVoltageService

        return DistributionVoltageService()

    elif name == 'EnergyMarketService':
        from services.energy_market_service.energy_market_service import EnergyMarketService

        energy_market = EnergyMarketService()
        return energy_market

    raise "There is no service with name: " + name

