def create_service(name):
    if name == 'Regulation':
        from services.reg_service.reg_service import RegService

        return RegService()

    elif name == 'ArtificialInertia':
        return None
