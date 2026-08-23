"""
Base service interface.
"""
from abc import ABC, abstractmethod

class BaseService(ABC):

    @abstractmethod
    def initialize(self)->None:
        ...

    @abstractmethod
    def shutdown(self)->None:
        ...
