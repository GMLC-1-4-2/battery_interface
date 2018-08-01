import inflection
import importlib

class FleetFactory(object):

    def get_instance(self, fleet_name):
        module_name = f"fleets.{fleet_name}.{fleet_name}"
        class_name = inflection.camelize(fleet_name)

        #print("module: ", module_name)
        #print("class_name: ", class_name)

        module = importlib.import_module(module_name)
        klass = getattr(module, class_name)
        return klass()
