import logging

_LOGGER = logging.getLogger(__name__)


class Microinverter:
    def __init__(self, micro_id, sn):
        self.id = micro_id
        self.sn = sn
        self.modules = []  # List of SolarModule objects

    def add_module(self, module):
        self.modules.append(module)

    def set_data(self, data):
        main = data[0]
        times = [i for i in main[1:] if isinstance(i, str)]
        module_data = [i for i in main[1:] if isinstance(i, list) and isinstance(i[1], list)]

        # TODO There is more data in main[1:] that might be useful

        for mod_data in module_data:

            port = mod_data[0]
            
            # Find the corresponding module by port
            module = self.find_module_by_port(port)
            if not module:
                _LOGGER.warning("Module with port %s not found in microinverter ID %s", port, self.id)
                continue

            module.set_data(mod_data[1], times)

    def find_module_by_port(self, port):
        for module in self.modules:
            if module.port == port:
                return module
        return None
    def __repr__(self):
        return f"Microinverter(id={self.id}, sn={self.sn}, modules={len(self.modules)})"