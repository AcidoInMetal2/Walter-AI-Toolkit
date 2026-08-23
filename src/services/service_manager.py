"""
Service container.
"""
class ServiceManager:
    def __init__(self):
        self._services={}

    def register(self,name:str,service):
        self._services[name]=service
        service.initialize()

    def get(self,name:str):
        return self._services.get(name)

    def shutdown(self):
        for service in self._services.values():
            service.shutdown()
