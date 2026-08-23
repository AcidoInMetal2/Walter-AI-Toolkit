"""
Simple publish/subscribe event bus.
"""
class EventBus:
    def __init__(self):
        self._events={}

    def subscribe(self,event:str,callback):
        self._events.setdefault(event,[]).append(callback)

    def publish(self,event:str,*args,**kwargs):
        for cb in self._events.get(event,[]):
            cb(*args,**kwargs)
