import yaml

class ConfigLoader:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)

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