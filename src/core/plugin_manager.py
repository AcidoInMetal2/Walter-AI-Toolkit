"""
Plugin manager.
"""
from .context import Context

class PluginManager:
    def __init__(self):
        self._plugins = {}

    def register(self, name:str, module)->None:
        self._plugins[name]=module

    def get(self,name:str):
        return self._plugins.get(name)

    def execute(self,name:str,context:Context)->Context:
        plugin=self.get(name)
        if plugin is None:
            raise KeyError(f"Plugin '{name}' no registrado.")
        return plugin.execute(context)
