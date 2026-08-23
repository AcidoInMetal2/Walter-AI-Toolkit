"""
Execution pipeline.
"""
from .dispatcher import Dispatcher
from .context import Context

class Pipeline:
    def __init__(self):
        self.dispatcher=Dispatcher()

    def register(self,module):
        self.dispatcher.register(module)

    def execute(self,context:Context)->Context:
        return self.dispatcher.dispatch(context)
