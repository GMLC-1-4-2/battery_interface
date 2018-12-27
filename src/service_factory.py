def create_service(name, **kwargs):
    if name == 'Regulation':
        from services.reg_service.reg_service import RegService

        return RegService()

    elif name == 'ArtificialInertia':
        return None

    raise "There is no service with name: " + name

