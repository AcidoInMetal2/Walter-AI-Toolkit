"""
Application bootstrap.
"""
from config.paths import create_directories
from .context import Context
from .pipeline import Pipeline

class Application:
    def __init__(self):
        create_directories()
        self.context=Context()
        self.pipeline=Pipeline()

    def run(self):
        return self.pipeline.execute(self.context)
