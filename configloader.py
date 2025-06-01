import os
import yaml

class ConfigLoader:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        if self.config is None and os.path.exists("config.yaml.sample"):
            self.config = self._load_config("config.yaml.sample")
        if self.config is None:
            exit(1)

    def _load_config(self, path):
        try:
            with open(path, "r") as file:
                print(f"using {path}")
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"{path} not found.")
        except yaml.YAMLError as e:
            print(f"error parsing {path}: {e}")
        return None
    
    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config

        for k in keys:
            value = value.get(k, {})
        return value if value else default
    
    def all_items_as_string(self):
        return self._dict_to_string(self.config)
    
    def _dict_to_string(self, d, prefix=''):
        items = []
        for key, value in d.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                items.append(self._dict_to_string(value, new_key))
            else:
                items.append(f"{new_key}: {value}")
        return "\n".join(items)
    
config = ConfigLoader()