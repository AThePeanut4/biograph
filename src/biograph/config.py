import yaml
from pydantic import BaseModel

_cache = {}


def get[T: BaseModel](cls: type[T], name: str) -> T:
    if name in _cache:
        return _cache[name]

    with open(f"config/{name}.yml") as f:
        cfg = yaml.safe_load(f)

    ret = cls.model_validate(cfg)
    _cache[name] = ret
    return ret
