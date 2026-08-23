"""
Module dispatcher.
"""
from .context import Context

class Dispatcher:
    def __init__(self):
        self._modules=[]

    def register(self,module):
        self._modules.append(module)

    def dispatch(self,context:Context)->Context:
        for module in self._modules:
            context=module.execute(context)
        return context
