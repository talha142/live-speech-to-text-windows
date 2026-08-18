import yaml
import os
import sys

class Config:
    def __init__(self, config_path="config.yaml"):
        # Handle PyInstaller bundle path
        self.base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        self.config_path = os.path.join(self.base_path, config_path)
        self.data = {}
        self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")
        
        with open(self.config_path, 'r') as f:
            self.data = yaml.safe_load(f)

    def get(self, key, default=None):
        keys = key.split('.')
        val = self.data
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

config = Config()
